
import json
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.db.models import (
    CampaignBudget,
    CustomerLoyaltyProfile,
    InventorySnapshot,
    RewardApproval,
    RewardCatalogue,
    RewardLedger,
    RewardProductMapping,
)
from backend.app.domain.eligibility import check_eligibility


def redeem_reward(db: Session, request):

    try:
        # 1. Prepare request hash
        request_data = {
            "approval_id": request.approval_id,
            "customer_id": request.customer_id,
            "reward_id": request.reward_id,
            "campaign_id": request.campaign_id,
        }

        request_hash = sha256(
            json.dumps(request_data, sort_keys=True).encode()
        ).hexdigest()

        # 2. Initial idempotency check
        existing = (
            db.query(RewardLedger)
            .filter(
                RewardLedger.idempotency_key == request.idempotency_key
            )
            .first()
        )

        if existing:
            if existing.request_hash != request_hash:
                raise ValueError(
                    "Idempotency key already used with different request"
                )
            return existing

        # 3. Lock approval
        approval = (
            db.query(RewardApproval)
            .filter(
                RewardApproval.approval_id == request.approval_id
            )
            .with_for_update()
            .first()
        )

        if approval is None:
            raise ValueError("Approval not found")

        # 4. Second idempotency check
        existing = (
            db.query(RewardLedger)
            .filter(
                RewardLedger.idempotency_key == request.idempotency_key
            )
            .first()
        )

        if existing:
            if existing.request_hash != request_hash:
                raise ValueError(
                    "Idempotency key already used with different request"
                )
            db.commit()
            return existing

        # 5. Validate approval
        if approval.approval_status != "APPROVED":
            raise ValueError("Approval is not available for redemption")

        if (
            approval.customer_id != request.customer_id
            or approval.reward_id != request.reward_id
            or approval.campaign_id != request.campaign_id
        ):
            raise ValueError("Request does not match approval")

        # 6. Lock reward
        reward = (
            db.query(RewardCatalogue)
            .filter(
                RewardCatalogue.reward_id == request.reward_id
            )
            .with_for_update()
            .first()
        )

        if reward is None:
            raise ValueError("Reward not found")

        if reward.campaign_id != request.campaign_id:
            raise ValueError("Reward does not belong to this campaign")

        # 7. Lock customer
        customer = (
            db.query(CustomerLoyaltyProfile)
            .filter(
                CustomerLoyaltyProfile.customer_id == request.customer_id
            )
            .with_for_update()
            .first()
        )

        if customer is None:
            raise ValueError("Customer not found")

        # 8. Lock campaign
        campaign = (
            db.query(CampaignBudget)
            .filter(
                CampaignBudget.campaign_id == request.campaign_id
            )
            .with_for_update()
            .first()
        )

        if campaign is None:
            raise ValueError("Campaign not found")

        # 9. Revalidate points and eligibility
        if customer.points_balance < approval.points_required:
            raise ValueError("Insufficient points balance")

        if campaign.campaign_status.lower() != "active":
            raise ValueError("Campaign is inactive")

        eligibility = check_eligibility(
            customer={
                "profile_status": customer.profile_status,
                "loyalty_tier": customer.loyalty_tier,
                "points_balance": customer.points_balance,
            },
            reward={
                "status": reward.status,
                "valid_from": reward.valid_from,
                "valid_until": reward.valid_until,
                "eligible_tiers": reward.eligible_tiers,
                "points_required": reward.points_required,
                "minimum_purchase_value": reward.minimum_purchase_value,
            },
            evaluation_date=approval.evaluation_date,
            purchase_value=approval.purchase_value,
        )

        if not eligibility["eligible"]:
            raise ValueError(
                "Redemption validation failed: "
                + ", ".join(eligibility["reason_codes"])
            )

        # 10. Check approved campaign budget
        if campaign.approved_amount < approval.reward_cost:
            raise ValueError("Approved campaign amount is insufficient")

        # 11. Lock inventory
        mappings = (
            db.query(RewardProductMapping)
            .filter(
                RewardProductMapping.reward_id == request.reward_id
            )
            .all()
        )

        inventory_rows = []

        for mapping in mappings:

            inventory = (
                db.query(InventorySnapshot)
                .filter(
                    InventorySnapshot.product_id == mapping.product_id
                )
                .with_for_update()
                .first()
            )

            if inventory is None:
                raise ValueError(
                    f"Inventory not found: {mapping.product_id}"
                )

            quantity = mapping.minimum_stock_required

            if inventory.reserved_stock < quantity:
                raise ValueError(
                    f"Reserved stock insufficient: {mapping.product_id}"
                )

            if inventory.on_hand_stock < quantity:
                raise ValueError(
                    f"On-hand stock insufficient: {mapping.product_id}"
                )

            inventory_rows.append((inventory, quantity))

        # 12. Debit points
        customer.points_balance -= approval.points_required

        # 13. Transfer campaign budget
        campaign.approved_amount -= approval.reward_cost
        campaign.committed_amount += approval.reward_cost

        # 14. Update inventory
        for inventory, quantity in inventory_rows:

            inventory.on_hand_stock -= quantity
            inventory.reserved_stock -= quantity

            inventory.available_stock = (
                inventory.on_hand_stock - inventory.reserved_stock
            )

        # 15. Create ledger entry
        redemption = RewardLedger(
            redemption_id=str(uuid4()),
            approval_id=approval.approval_id,
            idempotency_key=request.idempotency_key,
            request_hash=request_hash,
            customer_id=request.customer_id,
            reward_id=request.reward_id,
            campaign_id=request.campaign_id,
            points_debited=approval.points_required,
            reward_cost=approval.reward_cost,
            redemption_status="REDEEMED",
            created_at=datetime.now(UTC).replace(tzinfo=None),
            is_synthetic=customer.is_synthetic,
        )

        db.add(redemption)

        # 16. Update approval status
        approval.approval_status = "REDEEMED"

        # 17. Atomic commit
        db.commit()
        db.refresh(redemption)

        return redemption

    except Exception:
        db.rollback()
        raise
