
from backend.app.decision.constraints import (
    build_feasible_candidate_set,
    evaluate_hard_constraints,
)
from backend.app.decision.models import RewardCandidate


def get_candidate():
    return RewardCandidate(
        reward_id="SYN-REWARD-001",
        reward_name="Everyday Essentials",
        reward_type="product",
        reward_value=1730,
        points_required=1718,
        campaign_id="SYN-CAMP-001"
    )


def get_passing_results():
    return (
        {"eligible": True, "reason_codes": []},
        {"eligible": True, "reason_codes": []},
        {"eligible": True, "reason_codes": []}
    )


def test_all_constraints_pass():
    candidate = get_candidate()

    eligibility, inventory, budget = get_passing_results()

    result = evaluate_hard_constraints(
        candidate, eligibility, inventory, budget
    )

    assert result.eligible is True
    assert result.reason_codes == []


def test_eligibility_failure_rejects_candidate():
    candidate = get_candidate()

    eligibility, inventory, budget = get_passing_results()
    eligibility = {
        "eligible": False,
        "reason_codes": ["INSUFFICIENT_POINTS"]
    }

    result = evaluate_hard_constraints(
        candidate, eligibility, inventory, budget
    )

    assert result.eligible is False
    assert "INSUFFICIENT_POINTS" in result.reason_codes


def test_inventory_failure_rejects_candidate():
    candidate = get_candidate()

    eligibility, inventory, budget = get_passing_results()
    inventory = {
        "eligible": False,
        "reason_codes": ["INSUFFICIENT_STOCK"]
    }

    result = evaluate_hard_constraints(
        candidate, eligibility, inventory, budget
    )

    assert result.eligible is False
    assert "INSUFFICIENT_STOCK" in result.reason_codes


def test_budget_failure_rejects_candidate():
    candidate = get_candidate()

    eligibility, inventory, budget = get_passing_results()
    budget = {
        "eligible": False,
        "reason_codes": ["BUDGET_EXCEEDED"]
    }

    result = evaluate_hard_constraints(
        candidate, eligibility, inventory, budget
    )

    assert result.eligible is False
    assert "BUDGET_EXCEEDED" in result.reason_codes


def test_multiple_failures_are_collected():
    candidate = get_candidate()

    eligibility = {
        "eligible": False,
        "reason_codes": ["INSUFFICIENT_POINTS"]
    }

    inventory = {
        "eligible": False,
        "reason_codes": ["INSUFFICIENT_STOCK"]
    }

    budget = {
        "eligible": False,
        "reason_codes": ["BUDGET_EXCEEDED"]
    }

    result = evaluate_hard_constraints(
        candidate, eligibility, inventory, budget
    )

    assert result.eligible is False
    assert len(result.reason_codes) == 3


def test_missing_policy_result_rejects_candidate():
    candidate = get_candidate()

    eligibility, inventory, budget = get_passing_results()

    result = evaluate_hard_constraints(
        candidate, eligibility, None, budget
    )

    assert result.eligible is False
    assert "POLICY_RESULT_MISSING" in result.reason_codes


def test_feasible_candidate_set():
    candidate1 = get_candidate()
    candidate2 = get_candidate()
    candidate2.reward_id = "SYN-REWARD-002"

    eligibility, inventory, budget = get_passing_results()

    evaluate_hard_constraints(
        candidate1, eligibility, inventory, budget
    )

    evaluate_hard_constraints(
        candidate2,
        {"eligible": False, "reason_codes": ["INSUFFICIENT_POINTS"]},
        inventory,
        budget
    )

    feasible_candidates = build_feasible_candidate_set(
        [candidate1, candidate2]
    )

    assert len(feasible_candidates) == 1
    assert feasible_candidates[0].reward_id == "SYN-REWARD-001"
