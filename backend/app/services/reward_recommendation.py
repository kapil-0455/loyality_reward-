
from backend.app.decision.baseline_ranker import rank_rewards
from backend.app.decision.constraints import (
    build_feasible_candidate_set,
    evaluate_hard_constraints,
)
from backend.app.decision.models import RecommendationResult


def recommend_rewards(customer_id, evaluated_candidates):
    """
    Coordinates policy validation and baseline ranking.

    evaluated_candidates contains dictionaries with:
        candidate
        eligibility_result
        inventory_result
        budget_result
    """

    all_candidates = []
    all_reason_codes = []

    # 1. Apply hard constraints to every candidate
    for item in evaluated_candidates:

        candidate = item["candidate"]

        candidate = evaluate_hard_constraints(
            candidate=candidate,
            eligibility_result=item["eligibility_result"],
            inventory_result=item["inventory_result"],
            budget_result=item["budget_result"]
        )

        all_candidates.append(candidate)
        all_reason_codes.extend(candidate.reason_codes)

    # 2. Build feasible candidate set
    feasible_candidates = build_feasible_candidate_set(
        all_candidates
    )

    # 3. No eligible reward available
    if not feasible_candidates:
        return RecommendationResult(
            customer_id=customer_id,
            recommendations=[],
            status="NO_ELIGIBLE_REWARD",
            reason_codes=list(dict.fromkeys(all_reason_codes))
        )

    # 4. Rank feasible rewards
    ranked_rewards = rank_rewards(feasible_candidates)

    # 5. Return final recommendation
    return RecommendationResult(
        customer_id=customer_id,
        recommendations=ranked_rewards,
        status="SUCCESS",
        reason_codes=[]
    )
