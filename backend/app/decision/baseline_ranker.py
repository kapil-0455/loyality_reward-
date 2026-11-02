
from backend.app.decision.models import RankedReward
from backend.app.decision.objectives import calculate_reward_score


def rank_rewards(feasible_candidates):
    """
    Rank feasible reward candidates using the weighted objective.

    Each candidate must contain:
    relevance_score
    value_score
    inventory_score
    cost_penalty
    """

    ranked_rewards = []

    for candidate in feasible_candidates:

        # Safety check: invalid candidates must never be ranked
        if candidate.eligible is not True:
            continue

        if candidate.reason_codes:
            continue

        score = calculate_reward_score(
            relevance=candidate.relevance_score,
            reward_value=candidate.value_score,
            inventory_suitability=candidate.inventory_score,
            cost_penalty=candidate.cost_penalty
        )

        ranked_rewards.append(
            RankedReward(
                candidate=candidate,
                score=score
            )
        )

    # Highest score gets rank 1
    ranked_rewards.sort(
        key=lambda reward: reward.score,
        reverse=True
    )

    for index, reward in enumerate(ranked_rewards):
        reward.rank = index + 1

    return ranked_rewards
