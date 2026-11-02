
def check_campaign_budget(
    budget_limit,
    committed_amount,
    approved_amount,
    reward_cost,
    campaign_status
):
    # Validate budget values
    amounts = [
        budget_limit,
        committed_amount,
        approved_amount,
        reward_cost
    ]

    if any(amount < 0 for amount in amounts):
        raise ValueError("Budget amounts cannot be negative")

    if campaign_status.lower() != "active":
        return {
            "eligible": False,
            "available_budget": budget_limit - committed_amount - approved_amount,
            "reason_codes": ["CAMPAIGN_INACTIVE"]
        }

    # Calculate existing commitments
    active_commitments = committed_amount + approved_amount

    # Calculate available budget
    available_budget = budget_limit - active_commitments

    reason_codes = []

    # Check campaign budget
    if reward_cost > available_budget:
        reason_codes.append("BUDGET_EXCEEDED")

    return {
        "eligible": len(reason_codes) == 0,
        "available_budget": available_budget,
        "active_commitments": active_commitments,
        "reason_codes": reason_codes
    }
