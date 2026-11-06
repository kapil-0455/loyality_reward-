import math

try:
    from laya import Router
except ImportError:
    Router = None

from backend.app.decision.baseline_ranker import rank_rewards
from backend.app.decision.models import RankedReward
from backend.app.decision.objectives import calculate_reward_score

MIN_CONFIDENCE = 0.60


def select_reward_with_laya(
    customer_context,
    feasible_candidates,
    router=None
):
    """
    Select one feasible reward using Laya.

    Falls back to baseline ranking if Laya fails,
    is not installed, or returns an invalid/low-confidence decision.
    """

    if not feasible_candidates:
        return []

    # Safety: only eligible candidates are allowed
    candidates = [
        candidate
        for candidate in feasible_candidates
        if candidate.eligible is True
        and not candidate.reason_codes
    ]

    if not candidates:
        return []

    if Router is None and router is None:
        return rank_rewards(customer_context, candidates)

    try:
        if router is None:
            router = Router()

        # Prepare reward options for Laya
        criteria = {}

        for candidate in candidates:
            criteria[candidate.reward_id] = (
                f"{candidate.reward_name}, "
                f"type: {candidate.reward_type}, "
                f"value: {candidate.reward_value}, "
                f"points: {candidate.points_required}"
            )

        state = {
            **customer_context,
            "rewards": list(criteria.keys())
        }

        questions = {
            "reward_choice": {
                "type": "choice",
                "instructions": (
                    "Select the most suitable reward "
                    "for this customer and campaign."
                ),
                "criteria": criteria
            }
        }

        result = router.predict(
            state,
            questions,
            model="typed-decisions"
        )

        answer = result["answers"]["reward_choice"]
        selected_id = answer["choice"]
        confidence = float(answer["answer_confidence"])

        # A probability must be finite and within [0, 1].
        # NaN otherwise bypasses a simple confidence < threshold check.
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("Laya returned an invalid confidence value")

        candidate_map = {
            candidate.reward_id: candidate
            for candidate in candidates
        }

        if selected_id not in candidate_map:
            raise ValueError("Laya returned an unknown reward ID")

        if confidence < MIN_CONFIDENCE:
            raise ValueError("Laya confidence is too low")

        selected_candidate = candidate_map[selected_id]

        score = calculate_reward_score(
            relevance=selected_candidate.relevance_score,
            reward_value=selected_candidate.value_score,
            inventory_suitability=selected_candidate.inventory_score,
            cost_penalty=selected_candidate.cost_penalty
        )

        return [
            RankedReward(
                candidate=selected_candidate,
                score=score,
                rank=1
            )
        ]

    except Exception:  # noqa: BLE001
        return rank_rewards(candidates)
