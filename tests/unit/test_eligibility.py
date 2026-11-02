
from datetime import date
import pytest

from backend.app.domain.eligibility import check_eligibility


@pytest.fixture
def customer():
    return {
        "profile_status": "active",
        "loyalty_tier": "Gold",
        "points_balance": 5000,
    }


@pytest.fixture
def reward():
    return {
        "status": "active",
        "valid_from": date(2011, 11, 1),
        "valid_until": date(2012, 3, 31),
        "eligible_tiers": "Silver,Gold",
        "points_required": 1718,
        "minimum_purchase_value": 500,
    }


def test_eligible_customer(customer, reward):
    result = check_eligibility(
        customer,
        reward,
        date(2011, 12, 10),
        purchase_value=1000,
    )

    assert result["eligible"] is True
    assert result["reason_codes"] == []


def test_insufficient_points(customer, reward):
    customer["points_balance"] = 100

    result = check_eligibility(
        customer,
        reward,
        date(2011, 12, 10),
        purchase_value=1000,
    )

    assert result["eligible"] is False
    assert "INSUFFICIENT_POINTS" in result["reason_codes"]


def test_ineligible_tier(customer, reward):
    customer["loyalty_tier"] = "Bronze"

    result = check_eligibility(
        customer,
        reward,
        date(2011, 12, 10),
        purchase_value=1000,
    )

    assert result["eligible"] is False
    assert "TIER_NOT_ELIGIBLE" in result["reason_codes"]


def test_expired_reward(customer, reward):
    result = check_eligibility(
        customer,
        reward,
        date(2012, 4, 1),
        purchase_value=1000,
    )

    assert result["eligible"] is False
    assert "REWARD_EXPIRED" in result["reason_codes"]


def test_minimum_purchase_not_met(customer, reward):
    result = check_eligibility(
        customer,
        reward,
        date(2011, 12, 10),
        purchase_value=100,
    )

    assert result["eligible"] is False
    assert "MINIMUM_PURCHASE_NOT_MET" in result["reason_codes"]
