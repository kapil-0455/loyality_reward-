
from backend.app.decision.models import (
    RankedReward,
    RecommendationResult,
    RewardCandidate,
)


def test_reward_candidate_creation():
    candidate = RewardCandidate(
        reward_id="SYN-REWARD-001",
        reward_name="Everyday Essentials",
        reward_type="product",
        reward_value=1730,
        points_required=1718,
        campaign_id="SYN-CAMP-001"
    )

    assert candidate.reward_id == "SYN-REWARD-001"
    assert candidate.eligible is False
    assert candidate.reason_codes == []


def test_ranked_reward_creation():
    candidate = RewardCandidate(
        reward_id="SYN-REWARD-001",
        reward_name="Everyday Essentials",
        reward_type="product",
        reward_value=1730,
        points_required=1718,
        campaign_id="SYN-CAMP-001",
        eligible=True
    )

    ranked_reward = RankedReward(
        candidate=candidate,
        score=85.5,
        rank=1
    )

    assert ranked_reward.score == 85.5
    assert ranked_reward.rank == 1
    assert ranked_reward.candidate.eligible is True


def test_recommendation_result_creation():
    result = RecommendationResult(
        customer_id=12346
    )

    assert result.customer_id == 12346
    assert result.recommendations == []
    assert result.status == "SUCCESS"


def test_recommendation_with_ranked_rewards():
    candidate = RewardCandidate(
        reward_id="SYN-REWARD-001",
        reward_name="Everyday Essentials",
        reward_type="product",
        reward_value=1730,
        points_required=1718,
        campaign_id="SYN-CAMP-001",
        eligible=True
    )

    ranked = RankedReward(
        candidate=candidate,
        score=90.0,
        rank=1
    )

    result = RecommendationResult(
        customer_id=12346,
        recommendations=[ranked]
    )

    assert len(result.recommendations) == 1
    assert result.recommendations[0].rank == 1
    assert result.recommendations[0].candidate.reward_id == "SYN-REWARD-001"
