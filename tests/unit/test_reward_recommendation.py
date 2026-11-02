
from backend.app.decision.models import RewardCandidate
from backend.app.services.reward_recommendation import recommend_rewards


def create_candidate(reward_id, relevance=90):
    return RewardCandidate(
        reward_id=reward_id,
        reward_name="Test Reward",
        reward_type="product",
        reward_value=1000,
        points_required=500,
        campaign_id="SYN-CAMP-001",
        relevance_score=relevance,
        value_score=80,
        inventory_score=90,
        cost_penalty=20
    )


def passing_policy_results():
    return {
        "eligibility_result": {
            "eligible": True,
            "reason_codes": []
        },
        "inventory_result": {
            "eligible": True,
            "reason_codes": []
        },
        "budget_result": {
            "eligible": True,
            "reason_codes": []
        }
    }


def test_successful_recommendation():
    item = {
        "candidate": create_candidate("R1"),
        **passing_policy_results()
    }

    result = recommend_rewards(12346, [item])

    assert result.status == "SUCCESS"
    assert len(result.recommendations) == 1
    assert result.recommendations[0].candidate.reward_id == "R1"


def test_multiple_rewards_are_ranked():
    item1 = {
        "candidate": create_candidate("R1", relevance=50),
        **passing_policy_results()
    }

    item2 = {
        "candidate": create_candidate("R2", relevance=90),
        **passing_policy_results()
    }

    result = recommend_rewards(12346, [item1, item2])

    assert len(result.recommendations) == 2
    assert result.recommendations[0].candidate.reward_id == "R2"
    assert result.recommendations[0].rank == 1


def test_invalid_reward_is_excluded():
    item = {
        "candidate": create_candidate("R1"),
        **passing_policy_results()
    }

    item["inventory_result"] = {
        "eligible": False,
        "reason_codes": ["INSUFFICIENT_STOCK"]
    }

    result = recommend_rewards(12346, [item])

    assert result.status == "NO_ELIGIBLE_REWARD"
    assert result.recommendations == []
    assert "INSUFFICIENT_STOCK" in result.reason_codes


def test_no_candidates_available():
    result = recommend_rewards(12346, [])

    assert result.status == "NO_ELIGIBLE_REWARD"
    assert result.recommendations == []


def test_multiple_policy_failures():
    item = {
        "candidate": create_candidate("R1"),
        "eligibility_result": {
            "eligible": False,
            "reason_codes": ["INSUFFICIENT_POINTS"]
        },
        "inventory_result": {
            "eligible": False,
            "reason_codes": ["INSUFFICIENT_STOCK"]
        },
        "budget_result": {
            "eligible": False,
            "reason_codes": ["BUDGET_EXCEEDED"]
        }
    }

    result = recommend_rewards(12346, [item])

    assert result.status == "NO_ELIGIBLE_REWARD"
    assert len(result.reason_codes) == 3


def test_customer_id_is_preserved():
    result = recommend_rewards(12346, [])

    assert result.customer_id == 12346
