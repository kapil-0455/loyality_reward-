
from unittest.mock import Mock

from backend.app.agents.reward_agent import run_reward_agent


def test_reward_agent_returns_selected_reward():
    customer_context = {"customer_id": 101}
    candidates = [Mock(eligible=True, reason_codes=[])]
    selected_rewards = [Mock()]

    router = Mock()

    from unittest.mock import patch

    with patch(
        "backend.app.agents.reward_agent.select_reward_with_laya",
        return_value=selected_rewards
    ) as mock_selector:

        result = run_reward_agent(
            customer_context,
            candidates,
            router
        )

    assert result == selected_rewards
    mock_selector.assert_called_once_with(
        customer_context=customer_context,
        feasible_candidates=candidates,
        router=router
    )


def test_reward_agent_handles_empty_candidates():
    from unittest.mock import patch

    with patch(
        "backend.app.agents.reward_agent.select_reward_with_laya"
    ) as mock_selector:

        result = run_reward_agent({}, [])

    assert result == []
    mock_selector.assert_not_called()


def test_reward_agent_returns_baseline_fallback_result():
    from unittest.mock import patch

    candidates = [Mock()]
    baseline_result = [Mock()]

    with patch(
        "backend.app.agents.reward_agent.select_reward_with_laya",
        return_value=baseline_result
    ):

        result = run_reward_agent(
            {"customer_id": 101},
            candidates
        )

    assert result == baseline_result
