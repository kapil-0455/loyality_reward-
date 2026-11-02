
def evaluate_hard_constraints(
    candidate,
    eligibility_result,
    inventory_result,
    budget_result
):
    """
    Combines eligibility, inventory and budget results.
    A candidate is feasible only if all three checks pass.
    """

    policy_results = [
        eligibility_result,
        inventory_result,
        budget_result
    ]

    reason_codes = []

    for result in policy_results:

        # Fail closed if a policy result is missing
        if result is None:
            reason_codes.append("POLICY_RESULT_MISSING")
            continue

        if result.get("eligible") is not True:

            result_reasons = result.get("reason_codes", [])

            if result_reasons:
                reason_codes.extend(result_reasons)
            else:
                reason_codes.append("POLICY_CHECK_FAILED")

    # Remove duplicate reason codes
    reason_codes = list(dict.fromkeys(reason_codes))

    candidate.eligible = len(reason_codes) == 0
    candidate.reason_codes = reason_codes

    return candidate


def build_feasible_candidate_set(candidates):
    """
    Returns only candidates that passed all hard constraints.
    """

    return [
        candidate
        for candidate in candidates
        if candidate.eligible is True
        and not candidate.reason_codes
    ]
