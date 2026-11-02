
from datetime import datetime
from hashlib import sha256
import json
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.db.models import (
    CustomerLoyaltyProfile,
    RewardApproval,
    CampaignBudget,
    RewardProductMapping,
    InventorySnapshot,
    RewardLedger,
)


def redeem_reward(db: Session, request):

    try:
        request_data = {
            "approval_id": request.approval_id,
            "customer_id": request.customer_id,
            "reward_id": request.reward_id,
            "campaign_id": request.campaign_id,
        }

        request_hash = sha256(
            json.dumps(request_data, sort_keys=True).encode()
        ).hexdigest()

        # 1. First idempotency check
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

        # 2. Lock approval
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

        # 3. IMPORTANT: Check ledger again after acquiring lock
        # Another concurrent request may have completed redemption.
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

        if approval.approval_status != "APPROVED":
            raise ValueError("Approval is not available for redemption")

        # 4. Validate request against approval
        if (
            approval.customer_id != request.customer_id
            or approval.reward_id != request.reward_id
            or approval.campaign_id != request.campaign_id
        ):
            raise ValueError("Request does not match approval")

        # 5. Lock customer
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

        if customer.points_balance < approval.points_required:
            raise ValueError("Insufficient points balance")

        # 6. Lock campaign
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

        if campaign.approved_amount < approval.reward_cost:
            raise ValueError("Approved campaign amount is insufficient")

        # 7. Fetch and lock inventory
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

        # 8. Debit points
        customer.points_balance -= approval.points_required

        # 9. Transfer campaign budget
        campaign.approved_amount -= approval.reward_cost
        campaign.committed_amount += approval.reward_cost

        # 10. Update inventory
        for inventory, quantity in inventory_rows:

            inventory.on_hand_stock -= quantity
            inventory.reserved_stock -= quantity

            inventory.available_stock = (
                inventory.on_hand_stock - inventory.reserved_stock
            )

        # 11. Create ledger entry
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
            created_at=datetime.utcnow(),
            is_synthetic=customer.is_synthetic,
        )

        db.add(redemption)

        # 12. Update approval
        approval.approval_status = "REDEEMED"

        # 13. Commit all changes atomically
        db.commit()
        db.refresh(redemption)

        return redemption

    except Exception:
        db.rollback()
        raise
