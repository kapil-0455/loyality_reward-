from unittest.mock import Mock

import pytest

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
                "probabilities": {"R1": confidence, "R2": 1 - confidence},
                "confidence": confidence,
                "answer_confidence": confidence
            }
        }
    }
    return router


def get_candidates():
    return [
        create_candidate("R1", 50, 50, 50, 20),
        create_candidate("R2", 90, 90, 90, 10)
    ]


def test_laya_selects_valid_reward():
    router = create_mock_router("R1", 0.90)
    result = select_reward_with_laya({"customer_segment": "high_value"}, get_candidates(), router)
    assert len(result) == 1
    assert result[0].candidate.reward_id == "R1"
    assert result[0].rank == 1


def test_low_confidence_uses_baseline_fallback():
    router = create_mock_router("R1", 0.40)
    result = select_reward_with_laya({"customer_segment": "high_value"}, get_candidates(), router)
    assert result[0].candidate.reward_id == "R2"


def test_unknown_reward_id_uses_baseline_fallback():
    router = create_mock_router("UNKNOWN", 0.90)
    result = select_reward_with_laya({"customer_segment": "high_value"}, get_candidates(), router)
    assert result[0].candidate.reward_id == "R2"


def test_laya_exception_uses_baseline_fallback():
    router = Mock()
    router.predict.side_effect = RuntimeError("Laya failed")
    result = select_reward_with_laya({"customer_segment": "high_value"}, get_candidates(), router)
    assert result[0].candidate.reward_id == "R2"


def test_no_feasible_candidates():
    router = Mock()
    result = select_reward_with_laya({"customer_segment": "high_value"}, [], router)
    assert result == []
    router.predict.assert_not_called()


def test_confidence_exactly_at_threshold_is_accepted():
    router = create_mock_router("R1", 0.60)
    result = select_reward_with_laya({"customer_segment": "high_value"}, get_candidates(), router)
    assert result[0].candidate.reward_id == "R1"


@pytest.mark.parametrize("invalid_confidence", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_confidence_uses_baseline_fallback(invalid_confidence):
    router = create_mock_router("R1", invalid_confidence)
    result = select_reward_with_laya({"customer_segment": "high_value"}, get_candidates(), router)
    assert result[0].candidate.reward_id == "R2"


def test_malformed_laya_response_uses_baseline_fallback():
    router = Mock()
    router.predict.return_value = {"answers": {}}
    result = select_reward_with_laya({"customer_segment": "high_value"}, get_candidates(), router)
    assert result[0].candidate.reward_id == "R2"


def test_ineligible_candidate_is_not_sent_to_laya():
    candidates = get_candidates()
    candidates[0].eligible = False
    router = create_mock_router("R2", 0.90)
    result = select_reward_with_laya({"customer_segment": "high_value"}, candidates, router)
    sent_state = router.predict.call_args.args[0]
    assert sent_state["rewards"] == ["R2"]
    assert result[0].candidate.reward_id == "R2"


def test_all_ineligible_candidates_return_empty_result():
    candidates = get_candidates()
    for candidate in candidates:
        candidate.eligible = False
    router = Mock()
    result = select_reward_with_laya({"customer_segment": "high_value"}, candidates, router)
    assert result == []
    router.predict.assert_not_called()
