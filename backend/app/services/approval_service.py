
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.db.models import (
    CustomerLoyaltyProfile,
    RewardCatalogue,
    CampaignBudget,
    InventorySnapshot,
    RewardApproval,
    RewardProductMapping,
)

from backend.app.domain.eligibility import check_eligibility
from backend.app.domain.inventory import check_inventory
from backend.app.domain.budget import check_campaign_budget


def approve_reward(db: Session, request):

    request_data = {
        "customer_id": request.customer_id,
        "reward_id": request.reward_id,
        "campaign_id": request.campaign_id,
        "purchase_value": str(request.purchase_value),
        "evaluation_date": request.evaluation_date.isoformat(),
        "approved": request.approved,
    }

    request_hash = sha256(
        json.dumps(request_data, sort_keys=True).encode()
    ).hexdigest()

    try:
        # 1. Initial idempotency check
        existing = (
            db.query(RewardApproval)
            .filter(
                RewardApproval.idempotency_key == request.idempotency_key
            )
            .first()
        )

        if existing:
            if existing.request_hash != request_hash:
                raise ValueError(
                    "Idempotency key already used with different request"
                )
            return existing

        # 2. Lock customer
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

        # 3. Recheck idempotency after acquiring lock
        existing = (
            db.query(RewardApproval)
            .filter(
                RewardApproval.idempotency_key == request.idempotency_key
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

        # 4. Lock reward
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

        # 5. Lock campaign
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

        if reward.campaign_id != campaign.campaign_id:
            raise ValueError("Reward does not belong to this campaign")

        # 6. Eligibility check
        customer_data = {
            "profile_status": customer.profile_status,
            "loyalty_tier": customer.loyalty_tier,
            "points_balance": customer.points_balance,
        }

        reward_data = {
            "status": reward.status,
            "valid_from": reward.valid_from,
            "valid_until": reward.valid_until,
            "eligible_tiers": reward.eligible_tiers,
            "points_required": reward.points_required,
            "minimum_purchase_value": reward.minimum_purchase_value,
        }

        eligibility = check_eligibility(
            customer=customer_data,
            reward=reward_data,
            evaluation_date=request.evaluation_date,
            purchase_value=request.purchase_value,
        )

        if not eligibility["eligible"]:
            raise ValueError(
                "Eligibility failed: "
                + ", ".join(eligibility["reason_codes"])
            )

        # 7. Budget check
        budget_result = check_campaign_budget(
            budget_limit=campaign.budget_limit,
            committed_amount=campaign.committed_amount,
            approved_amount=campaign.approved_amount,
            reward_cost=reward.reward_value,
            campaign_status=campaign.campaign_status,
        )

        if not budget_result["eligible"]:
            raise ValueError(
                "Budget check failed: "
                + ", ".join(budget_result["reason_codes"])
            )

        # 8. Inventory check
        mappings = (
            db.query(RewardProductMapping)
            .filter(
                RewardProductMapping.reward_id == reward.reward_id
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
                    f"Inventory not found for product {mapping.product_id}"
                )

            inventory_result = check_inventory(
                on_hand_stock=inventory.on_hand_stock,
                reserved_stock=inventory.reserved_stock,
                required_quantity=mapping.minimum_stock_required,
                minimum_stock_level=inventory.reorder_level,
                replenishment_date=inventory.replenishment_date,
                evaluation_date=request.evaluation_date,
            )

            if not inventory_result["eligible"]:
                raise ValueError(
                    "Inventory check failed: "
                    + ", ".join(inventory_result["reason_codes"])
                )

            inventory_rows.append(
                (inventory, mapping.minimum_stock_required)
            )

        # 9. Create approval
        approval = RewardApproval(
            approval_id=str(uuid4()),
            idempotency_key=request.idempotency_key,
            request_hash=request_hash,
            customer_id=request.customer_id,
            reward_id=reward.reward_id,
            campaign_id=campaign.campaign_id,
            purchase_value=request.purchase_value,
            evaluation_date=request.evaluation_date,
            points_required=reward.points_required,
            reward_cost=reward.reward_value,
            approval_status="APPROVED" if request.approved else "REJECTED",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        db.add(approval)

        # 10. Reserve budget and inventory
        if request.approved:
            campaign.approved_amount += reward.reward_value

            for inventory, quantity in inventory_rows:
                inventory.reserved_stock += quantity
                inventory.available_stock = (
                    inventory.on_hand_stock - inventory.reserved_stock
                )

        # 11. Commit transaction
        db.commit()
        db.refresh(approval)

        return approval

    except IntegrityError:
        db.rollback()

        # Handle a concurrent request using the same unique key
        existing = (
            db.query(RewardApproval)
            .filter(
                RewardApproval.idempotency_key == request.idempotency_key
            )
            .first()
        )

        if existing:
            if existing.request_hash != request_hash:
                raise ValueError(
                    "Idempotency key already used with different request"
                )
            return existing

        raise

    except Exception:
        db.rollback()
        raise
