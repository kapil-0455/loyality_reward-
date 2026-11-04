from backend.app.decision.laya_adapter import select_reward_with_laya


def run_reward_agent(customer_context, feasible_candidates, router=None):
    """
    Reward Agent:
    Selects the most suitable reward from feasible candidates.

    Laya handles decision-making.
    Baseline ranker is used as a fallback
    through the Laya adapter.
    """

    if not feasible_candidates:
        return []

    selected_rewards = select_reward_with_laya(
        customer_context=customer_context,
        feasible_candidates=feasible_candidates,
        router=router,
    )

    return selected_rewards
