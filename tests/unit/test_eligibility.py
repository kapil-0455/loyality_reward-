
from backend.app.domain.eligibility import check_eligibility


def get_customer():
    return {
        "customer_id": 12346,
        "loyalty_tier": "Platinum",
        "points_balance": 5000,
        "profile_status": "active"
    }


def get_reward():
    return {
        "reward_id": "SYN-REWARD-001",
        "points_required": 1718,
        "eligible_tiers": "Silver,Gold",
        "valid_from": "2011-11-01",
        "valid_until": "2012-03-31",
        "minimum_purchase_value": 0,
        "status": "active"
    }


def test_ineligible_customer_tier():
    result = check_eligibility(
        get_customer(),
        get_reward(),
        evaluation_date="2011-12-10",
        purchase_value=1000
    )

    assert result["eligible"] is False
    assert "TIER_NOT_ELIGIBLE" in result["reason_codes"]


def test_insufficient_points():
    customer = get_customer()
    customer["points_balance"] = 100

    result = check_eligibility(
        customer,
        get_reward(),
        evaluation_date="2011-12-10",
        purchase_value=1000
    )

    assert result["eligible"] is False
    assert "INSUFFICIENT_POINTS" in result["reason_codes"]


def test_inactive_customer():
    customer = get_customer()
    customer["profile_status"] = "inactive"

    result = check_eligibility(
        customer,
        get_reward(),
        evaluation_date="2011-12-10",
        purchase_value=1000
    )

    assert result["eligible"] is False
    assert "CUSTOMER_INACTIVE" in result["reason_codes"]


def test_reward_expired():
    result = check_eligibility(
        get_customer(),
        get_reward(),
        evaluation_date="2012-04-01",
        purchase_value=1000
    )

    assert result["eligible"] is False
    assert "REWARD_EXPIRED" in result["reason_codes"]


def test_reward_not_yet_valid():
    result = check_eligibility(
        get_customer(),
        get_reward(),
        evaluation_date="2011-10-31",
        purchase_value=1000
    )

    assert result["eligible"] is False
    assert "REWARD_NOT_YET_VALID" in result["reason_codes"]


def test_minimum_purchase_not_met():
    reward = get_reward()
    reward["minimum_purchase_value"] = 1000

    result = check_eligibility(
        get_customer(),
        reward,
        evaluation_date="2011-12-10",
        purchase_value=500
    )

    assert result["eligible"] is False
    assert "MINIMUM_PURCHASE_NOT_MET" in result["reason_codes"]


def test_eligible_customer():
    customer = get_customer()
    customer["loyalty_tier"] = "Gold"

    result = check_eligibility(
        customer,
        get_reward(),
        evaluation_date="2011-12-10",
        purchase_value=1000
    )

    assert result["eligible"] is True
    assert result["reason_codes"] == []

