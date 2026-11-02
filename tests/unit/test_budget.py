
import pytest

from backend.app.domain.budget import check_campaign_budget


def test_sufficient_campaign_budget():
    result = check_campaign_budget(
        budget_limit=50000,
        committed_amount=5000,
        approved_amount=0,
        reward_cost=10000,
        campaign_status="active"
    )

    assert result["eligible"] is True
    assert result["available_budget"] == 45000
    assert result["reason_codes"] == []


def test_insufficient_campaign_budget():
    result = check_campaign_budget(
        budget_limit=50000,
        committed_amount=40000,
        approved_amount=5000,
        reward_cost=10000,
        campaign_status="active"
    )

    assert result["eligible"] is False
    assert result["available_budget"] == 5000
    assert "BUDGET_EXCEEDED" in result["reason_codes"]


def test_inactive_campaign():
    result = check_campaign_budget(
        budget_limit=50000,
        committed_amount=5000,
        approved_amount=0,
        reward_cost=1000,
        campaign_status="scheduled"
    )

    assert result["eligible"] is False
    assert "CAMPAIGN_INACTIVE" in result["reason_codes"]


def test_approved_amount_is_counted():
    result = check_campaign_budget(
        budget_limit=50000,
        committed_amount=10000,
        approved_amount=15000,
        reward_cost=26000,
        campaign_status="active"
    )

    assert result["available_budget"] == 25000
    assert result["eligible"] is False
    assert "BUDGET_EXCEEDED" in result["reason_codes"]


def test_zero_cost_reward():
    result = check_campaign_budget(
        budget_limit=50000,
        committed_amount=5000,
        approved_amount=0,
        reward_cost=0,
        campaign_status="active"
    )

    assert result["eligible"] is True


def test_negative_budget_rejected():
    with pytest.raises(ValueError):
        check_campaign_budget(
            budget_limit=50000,
            committed_amount=-100,
            approved_amount=0,
            reward_cost=1000,
            campaign_status="active"
        )
