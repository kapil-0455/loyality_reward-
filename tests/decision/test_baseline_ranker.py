
from backend.app.decision.baseline_ranker import rank_rewards
from backend.app.decision.models import RewardCandidate


def create_candidate(reward_id, relevance, value, inventory, cost):
    return RewardCandidate(
        reward_id=reward_id,
        reward_name="Test Reward",
        reward_type="product",
        reward_value=1000,
        points_required=500,
        campaign_id="SYN-CAMP-001",
        eligible=True,
        relevance_score=relevance,
        value_score=value,
        inventory_score=inventory,
        cost_penalty=cost
    )


def test_rewards_are_ranked_by_score():
    candidates = [
        create_candidate("R1", 50, 50, 50, 20),
        create_candidate("R2", 90, 90, 90, 10),
        create_candidate("R3", 70, 70, 70, 20)
    ]

    result = rank_rewards(candidates)

    assert result[0].candidate.reward_id == "R2"
    assert result[0].rank == 1
    assert result[1].rank == 2
    assert result[2].rank == 3


def test_invalid_candidates_are_excluded():
    candidates = [
        create_candidate("R1", 90, 90, 90, 10),
        create_candidate("R2", 80, 80, 80, 10)
    ]

    candidates[1].eligible = False

    result = rank_rewards(candidates)

    assert len(result) == 1
    assert result[0].candidate.reward_id == "R1"


def test_candidates_with_reason_codes_are_excluded():
    candidate = create_candidate("R1", 90, 90, 90, 10)
    candidate.reason_codes = ["INSUFFICIENT_STOCK"]

    result = rank_rewards([candidate])

    assert result == []


def test_empty_candidate_list():
    result = rank_rewards([])

    assert result == []


def test_rank_order_is_descending():
    candidates = [
        create_candidate("R1", 50, 50, 50, 20),
        create_candidate("R2", 90, 90, 90, 10)
    ]

    result = rank_rewards(candidates)

    assert result[0].score >= result[1].score


def test_rank_assignments_are_sequential():
    candidates = [
        create_candidate("R1", 50, 50, 50, 20),
        create_candidate("R2", 90, 90, 90, 10),
        create_candidate("R3", 70, 70, 70, 20)
    ]

    result = rank_rewards(candidates)

    assert [reward.rank for reward in result] == [1, 2, 3]
