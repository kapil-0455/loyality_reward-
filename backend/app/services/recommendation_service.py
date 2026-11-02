from backend.app.db.models import RewardProductMapping
from backend.app.db.repositories.campaign_repository import get_campaign_by_id
from backend.app.db.repositories.customer_repository import get_customer_by_id
from backend.app.db.repositories.inventory_repository import get_product_inventory
from backend.app.db.repositories.reward_repository import get_active_rewards
from backend.app.decision.models import RewardCandidate
from backend.app.domain.budget import check_campaign_budget
from backend.app.domain.eligibility import check_eligibility
from backend.app.domain.inventory import check_inventory
from backend.app.services.reward_recommendation import recommend_rewards


def get_recommendations(db, customer_id, purchase_value, evaluation_date):
    # 1. Fetch customer
    customer = get_customer_by_id(db, customer_id)

    if customer is None:
        return {
            "customer_id": customer_id,
            "status": "CUSTOMER_NOT_FOUND",
            "recommendations": [],
            "reason_codes": [],
        }

    customer_data = {
        "customer_id": int(customer.customer_id),
        "loyalty_tier": customer.loyalty_tier,
        "points_balance": customer.points_balance,
        "profile_status": customer.profile_status,
    }

    # 2. Fetch active rewards
    rewards = get_active_rewards(db)
    evaluated_candidates = []

    for reward in rewards:
        campaign = get_campaign_by_id(db, reward.campaign_id)
        if campaign is None:
            continue

        reward_data = {
            "reward_id": reward.reward_id,
            "reward_name": reward.reward_name,
            "reward_type": reward.reward_type,
            "reward_value": float(reward.reward_value),
            "points_required": reward.points_required,
            "eligible_tiers": reward.eligible_tiers,
            "valid_from": reward.valid_from,
            "valid_until": reward.valid_until,
            "minimum_purchase_value": (
                float(reward.minimum_purchase_value)
                if reward.minimum_purchase_value is not None
                else None
            ),
            "status": reward.status,
        }

        eligibility_result = check_eligibility(
            customer=customer_data,
            reward=reward_data,
            evaluation_date=evaluation_date,
            purchase_value=purchase_value,
        )

        # A reward without a product mapping has no inventory constraint.
        inventory_result = {"eligible": True, "reason_codes": []}

        mappings = (
            db.query(RewardProductMapping)
            .filter(RewardProductMapping.reward_id == reward.reward_id)
            .all()
        )

        for mapping in mappings:
            inventory = get_product_inventory(db, mapping.product_id)

            if inventory is None:
                inventory_result = {
                    "eligible": False,
                    "reason_codes": ["INSUFFICIENT_STOCK"],
                }
                break

            inventory_result = check_inventory(
                on_hand_stock=inventory.on_hand_stock,
                reserved_stock=inventory.reserved_stock,
                required_quantity=mapping.minimum_stock_required,
                minimum_stock_level=inventory.reorder_level,
                replenishment_date=inventory.replenishment_date,
                replenishment_quantity=0,
                evaluation_date=evaluation_date,
            )

            if not inventory_result.get("eligible", False):
                break

        budget_result = check_campaign_budget(
            budget_limit=campaign.budget_limit,
            committed_amount=campaign.committed_amount,
            approved_amount=campaign.approved_amount,
            reward_cost=reward.reward_value,
            campaign_status=campaign.campaign_status,
        )

        # Temporary baseline scores; calibrate these from real features later.
        candidate = RewardCandidate(
            reward_id=reward.reward_id,
            reward_name=reward.reward_name,
            reward_type=reward.reward_type,
            reward_value=float(reward.reward_value),
            points_required=reward.points_required,
            campaign_id=reward.campaign_id,
            relevance_score=50,
            value_score=50,
            inventory_score=50,
            cost_penalty=50,
        )

        # Pass the exact dictionary contract expected by Day 3 service.
        # Do not call evaluate_hard_constraints() here; it is called there.
        evaluated_candidates.append({
            "candidate": candidate,
            "eligibility_result": eligibility_result,
            "inventory_result": inventory_result,
            "budget_result": budget_result,
        })

    return recommend_rewards(
        customer_id=customer_id,
        evaluated_candidates=evaluated_candidates,
    )
