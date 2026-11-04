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
    # Validate customer, reward and campaign data
    if not all(isinstance(data, dict) for data in [customer, reward, campaign]):
        return {"status": "INVALID_INPUT", "candidate": None}

    # Inventory can be a dictionary, list or None
    if inventory is not None and not isinstance(inventory, (dict, list)):
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
        inventory_checks = []

        if inventory is None:
            inventory_items = []

        elif isinstance(inventory, dict):
            inventory_items = [inventory]

        else:
            inventory_items = inventory

        # No product mapping means no inventory constraint
        if not inventory_items:
            inventory_result = {"eligible": True, "reason_codes": [], "checks": []}

        else:
            for item in inventory_items:
                if not isinstance(item, dict):
                    raise ValueError("Each inventory item must be a dictionary")

                result = check_inventory(
                    on_hand_stock=item["on_hand_stock"],
                    reserved_stock=item["reserved_stock"],
                    required_quantity=item["required_quantity"],
                    minimum_stock_level=item.get("minimum_stock_level", 0),
                    replenishment_date=item.get("replenishment_date"),
                    replenishment_quantity=item.get("replenishment_quantity", 0),
                    evaluation_date=evaluation_date,
                )

                inventory_checks.append(
                    {"product_id": item.get("product_id"), **result}
                )

            inventory_reason_codes = []

            for result in inventory_checks:
                inventory_reason_codes.extend(result["reason_codes"])

            # Remove duplicate reason codes
            inventory_reason_codes = list(dict.fromkeys(inventory_reason_codes))

            inventory_result = {
                "eligible": all(result["eligible"] for result in inventory_checks),
                "reason_codes": inventory_reason_codes,
                "checks": inventory_checks,
            }

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

    except Exception as error:
        return {"status": "ELIGIBILITY_ERROR", "error": str(error), "candidate": None}
