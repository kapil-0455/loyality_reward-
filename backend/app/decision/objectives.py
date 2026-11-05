import math


def calculate_reward_score(
    relevance,
    reward_value,
    inventory_suitability,
    cost_penalty
):
    """
    Calculate reward score using weighted objectives.

    All input values must be finite numbers between 0 and 100.
    """

    values = [
        relevance,
        reward_value,
        inventory_suitability,
        cost_penalty
    ]

    if any(
        not math.isfinite(value) or value < 0 or value > 100
        for value in values
    ):
        raise ValueError("All objective values must be finite numbers between 0 and 100")

    score = (
        0.35 * relevance
        + 0.30 * reward_value
        + 0.20 * inventory_suitability
        - 0.15 * cost_penalty
    )

    return round(score, 2)
