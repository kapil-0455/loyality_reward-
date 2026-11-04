"""
Eligibility Agent
Runs deterministic customer, reward, inventory
and campaign budget checks.
"""

from backend.app.decision.constraints import evaluate_hard_constraints
from backend.app.decision.models import RewardCandidate
from backend.app.domain.budget import check_campaign_budget
from backend.app.domain.eligibility import check_eligibility
from backend.app.domain.inventory import check_inventory


def run_eligibility_agent(
    customer, reward, inventory, campaign, evaluation_date, purchase_value=0
):
    # Validate input data
    if not all(
        isinstance(data, dict) for data in [customer, reward, inventory, campaign]
    ):
        return {"status": "INVALID_INPUT", "candidate": None}

    try:
        # 1. Customer and reward eligibility
        eligibility_result = check_eligibility(
            customer=customer,
            reward=reward,
            evaluation_date=evaluation_date,
            purchase_value=purchase_value,
        )

        # 2. Inventory availability
        inventory_result = check_inventory(
            on_hand_stock=inventory["on_hand_stock"],
            reserved_stock=inventory["reserved_stock"],
            required_quantity=inventory["required_quantity"],
            minimum_stock_level=inventory.get("minimum_stock_level", 0),
            replenishment_date=inventory.get("replenishment_date"),
            replenishment_quantity=inventory.get("replenishment_quantity", 0),
            evaluation_date=evaluation_date,
        )

        # 3. Campaign budget availability
        budget_result = check_campaign_budget(
            budget_limit=campaign["budget_limit"],
            committed_amount=campaign["committed_amount"],
            approved_amount=campaign["approved_amount"],
            reward_cost=reward["reward_cost"],
            campaign_status=campaign["status"],
        )

        # 4. Create reward candidate
        candidate = RewardCandidate(
            reward_id=str(reward["reward_id"]),
            reward_name=reward["reward_name"],
            reward_type=reward["reward_type"],
            reward_value=reward["reward_value"],
            points_required=reward["points_required"],
            campaign_id=str(reward["campaign_id"]),
        )

        # 5. Combine all hard constraints
        candidate = evaluate_hard_constraints(
            candidate=candidate,
            eligibility_result=eligibility_result,
            inventory_result=inventory_result,
            budget_result=budget_result,
        )

        return {
            "status": "SUCCESS",
            "eligible": candidate.eligible,
            "reason_codes": candidate.reason_codes,
            "candidate": candidate,
            "policy_results": {
                "eligibility": eligibility_result,
                "inventory": inventory_result,
                "budget": budget_result,
            },
        }

    except (KeyError, TypeError, ValueError) as error:
        return {"status": "VALIDATION_ERROR", "error": str(error), "candidate": None}

    except Exception as error:  # noqa: BLE001
        return {"status": "ELIGIBILITY_ERROR", "error": str(error), "candidate": None}
