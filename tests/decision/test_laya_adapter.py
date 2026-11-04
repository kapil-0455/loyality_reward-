
from unittest.mock import Mock

from backend.app.decision.laya_adapter import select_reward_with_laya
from backend.app.decision.models import RewardCandidate


def create_candidate(reward_id, relevance, value, inventory, cost):
    return RewardCandidate(
        reward_id=reward_id,
        reward_name=f"Reward {reward_id}",
        reward_type="discount",
        reward_value=100,
        points_required=200,
        campaign_id="CAMP-001",
        relevance_score=relevance,
        value_score=value,
        inventory_score=inventory,
        cost_penalty=cost,
        eligible=True,
        reason_codes=[]
    )


def create_mock_router(choice="R1", confidence=0.90):
    router = Mock()

    router.predict.return_value = {
        "answers": {
            "reward_choice": {
                "type": "choice",
                "choice": choice,
                "probabilities": {
                    "R1": confidence,
                    "R2": 1 - confidence
                },
                "confidence": confidence,
                "answer_confidence": confidence
            }
        }
    }

    return router


def test_laya_selects_valid_reward():
    candidates = [
        create_candidate("R1", 70, 70, 70, 20),
        create_candidate("R2", 80, 80, 80, 10)
    ]

    router = create_mock_router("R1", 0.90)

    result = select_reward_with_laya(
        {"customer_segment": "high_value"},
        candidates,
        router
    )

    assert len(result) == 1
    assert result[0].candidate.reward_id == "R1"
    assert result[0].rank == 1


def test_low_confidence_uses_baseline_fallback():
    candidates = [
        create_candidate("R1", 50, 50, 50, 20),
        create_candidate("R2", 90, 90, 90, 10)
    ]

    router = create_mock_router("R1", 0.40)

    result = select_reward_with_laya(
        {"customer_segment": "high_value"},
        candidates,
        router
    )

    assert result[0].candidate.reward_id == "R2"


def test_unknown_reward_id_uses_baseline_fallback():
    candidates = [
        create_candidate("R1", 50, 50, 50, 20),
        create_candidate("R2", 90, 90, 90, 10)
    ]

    router = create_mock_router("UNKNOWN", 0.90)

    result = select_reward_with_laya(
        {"customer_segment": "high_value"},
        candidates,
        router
    )

    assert result[0].candidate.reward_id == "R2"


def test_laya_exception_uses_baseline_fallback():
    candidates = [
        create_candidate("R1", 50, 50, 50, 20),
        create_candidate("R2", 90, 90, 90, 10)
    ]

    router = Mock()
    router.predict.side_effect = RuntimeError("Laya failed")

    result = select_reward_with_laya(
        {"customer_segment": "high_value"},
        candidates,
        router
    )

    assert result[0].candidate.reward_id == "R2"


def test_no_feasible_candidates():
    router = Mock()

    result = select_reward_with_laya(
        {"customer_segment": "high_value"},
        [],
        router
    )

    assert result == []
    router.predict.assert_not_called()
