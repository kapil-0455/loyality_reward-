
from datetime import date, datetime


def convert_to_date(value):
    """Convert string or datetime into date."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value))


def check_eligibility(
    customer,
    reward,
    evaluation_date,
    purchase_value=0
):
    reason_codes = []

    # 1. Check customer profile status
    if customer["profile_status"].lower() != "active":
        reason_codes.append("CUSTOMER_INACTIVE")

    # 2. Check reward status
    if reward["status"].lower() != "active":
        reason_codes.append("REWARD_INACTIVE")

    # 3. Check reward validity period
    evaluation_date = convert_to_date(evaluation_date)
    valid_from = convert_to_date(reward["valid_from"])
    valid_until = convert_to_date(reward["valid_until"])

    if evaluation_date < valid_from:
        reason_codes.append("REWARD_NOT_YET_VALID")

    elif evaluation_date > valid_until:
        reason_codes.append("REWARD_EXPIRED")

    # 4. Check customer tier
    customer_tier = customer["loyalty_tier"]

    eligible_tiers = [
        tier.strip()
        for tier in reward["eligible_tiers"].split(",")
    ]

    if customer_tier not in eligible_tiers:
        reason_codes.append("TIER_NOT_ELIGIBLE")

    # 5. Check available points
    if customer["points_balance"] < reward["points_required"]:
        reason_codes.append("INSUFFICIENT_POINTS")

    # 6. Check minimum purchase requirement
    minimum_purchase = reward["minimum_purchase_value"]

    if purchase_value < minimum_purchase:
        reason_codes.append("MINIMUM_PURCHASE_NOT_MET")

    return {
        "eligible": len(reason_codes) == 0,
        "reason_codes": reason_codes
   }
