
import pytest

from backend.app.domain.budget import check_campaign_budget


def test_sufficient_budget():
    result = check_campaign_budget(
        budget_limit=50000,
        committed_amount=5000,
        approved_amount=1000,
        reward_cost=1730,
        campaign_status="active",
    )

    assert result["eligible"] is True
    assert result["available_budget"] == 44000


def test_budget_exceeded():
    result = check_campaign_budget(
        budget_limit=10000,
        committed_amount=8000,
        approved_amount=1000,
        reward_cost=2000,
        campaign_status="active",
    )

    assert result["eligible"] is False
    assert "BUDGET_EXCEEDED" in result["reason_codes"]


def test_inactive_campaign():
    result = check_campaign_budget(
        budget_limit=50000,
        committed_amount=5000,
        approved_amount=1000,
        reward_cost=1730,
        campaign_status="inactive",
    )

    assert result["eligible"] is False
    assert "CAMPAIGN_INACTIVE" in result["reason_codes"]


def test_negative_budget():
    with pytest.raises(ValueError):
        check_campaign_budget(
            budget_limit=-1000,
            committed_amount=0,
            approved_amount=0,
            reward_cost=100,
            campaign_status="active",
        )
