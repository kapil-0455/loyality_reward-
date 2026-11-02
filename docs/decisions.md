# Day 3 -- Policy Engine and Decision Layer Decisions

## 1. Purpose

Day 3 implements the deterministic policy engine and a baseline
reward-ranking flow. Business rules determine which rewards are
feasible. The baseline ranker only orders feasible candidates; it does
not override eligibility, inventory, or campaign-budget rules.

## 2. Eligibility Rules

Implemented in `backend/app/domain/eligibility.py`.

A reward candidate is checked against:

-   Customer profile status must be `active`.
-   Reward status must be `active`.
-   Evaluation date must fall within `valid_from` and `valid_until`.
-   Customer loyalty tier must appear in the reward's comma-separated
    `eligible_tiers`.
-   Customer `points_balance` must be at least `points_required`.
-   Purchase value must meet `minimum_purchase_value`.

Rejection reason codes currently implemented:

-   `CUSTOMER_INACTIVE`
-   `REWARD_INACTIVE`
-   `REWARD_NOT_YET_VALID`
-   `REWARD_EXPIRED`
-   `TIER_NOT_ELIGIBLE`
-   `INSUFFICIENT_POINTS`
-   `MINIMUM_PURCHASE_NOT_MET`

The evaluation date is passed explicitly to the function. It is not
silently taken from the machine's current date. This matters because the
generated reward catalogue contains historical validity dates.

## 3. Inventory Assumptions

Implemented in `backend/app/domain/inventory.py`.

`available_to_promise = on_hand_stock - reserved_stock`

The function checks requested quantity against available-to-promise
stock, remaining stock against the configured minimum stock level, and
replenishment date/quantity when supplied. Negative stock/quantity
values and reserved stock greater than on-hand stock are rejected as
invalid inputs.

A future replenishment is not treated as available on the evaluation
date. Replenishment can only be counted when its date is on or before
the evaluation date.

Current rejection reason codes:

-   `INSUFFICIENT_STOCK`
-   `REPLENISHMENT_CONSTRAINT`

The caller must supply the correct `required_quantity` for the
reward/product mapping.

## 4. Campaign Budget Assumptions

Implemented in `backend/app/domain/budget.py`.

The current convention counts both committed and approved amounts as
existing commitments:

`active_commitments = committed_amount + approved_amount`

`available_budget = budget_limit - active_commitments`

The campaign must have status `active`, and requested `reward_cost` must
not exceed available budget. Negative budget amounts are rejected.

Rejection reason codes:

-   `CAMPAIGN_INACTIVE`
-   `BUDGET_EXCEEDED`

This convention must be used consistently in recommendation, approval,
and final redemption. Database-level atomic updates/locking are still
required to prevent concurrent overspending; this Day 3 function alone
does not provide concurrency safety.

## 5. Hard Constraints and Feasible Candidate Set

Implemented in `backend/app/decision/constraints.py`.

Eligibility, inventory, and budget results are combined. A candidate is
feasible only when all three policy results explicitly have
`eligible == True` and the candidate has no rejection reason codes.

If a policy result is missing, the candidate fails closed with
`POLICY_RESULT_MISSING`. If a failed policy result contains no reason
code, `POLICY_CHECK_FAILED` is used.

Duplicate reason codes are removed. `build_feasible_candidate_set`
returns only candidates with `eligible == True` and an empty
`reason_codes` list. A candidate that fails any hard constraint must not
enter ranking.

## 6. Baseline Ranking Objective

Implemented in `backend/app/decision/objectives.py`.

`Score = 0.35 × R + 0.30 × V + 0.20 × I - 0.15 × C`

Where R = customer relevance (0--100), V = reward value (0--100), I =
inventory suitability (0--100), and C = campaign cost penalty (0--100).

All inputs are validated to be within 0--100. The score is rounded to
two decimal places.

These are initial baseline weights, not empirically validated
business-optimal weights. They should be evaluated against suitable
business outcomes before being treated as optimal.

## 7. Baseline Ranker

Implemented in `backend/app/decision/baseline_ranker.py`.

-   Only candidates marked eligible with no reason codes are considered.
-   Each candidate is scored using the objective function.
-   Candidates are sorted by descending score.
-   Rank numbering starts at 1.
-   Invalid candidates are excluded.

The ranker does not perform eligibility, inventory, or budget
calculations itself. Those policy results must be evaluated before
ranking.

## 8. Recommendation Service

Implemented in `backend/app/services/reward_recommendation.py`.

The service coordinates supplied policy results, applies hard
constraints, builds the feasible candidate set, invokes the baseline
ranker, and returns a `RecommendationResult`.

If no feasible candidate remains, the service returns status
`NO_ELIGIBLE_REWARD`.

Current service boundary: it receives already-evaluated
candidate/policy-result dictionaries. Fetching records from
Neon/PostgreSQL and invoking domain checks from repository data are
integration work for the API/database phase.

## 9. Day 3 Validation

The following test modules were created and run successfully according
to the development session:

-   `tests/unit/test_eligibility.py`
-   `tests/unit/test_inventory.py`
-   `tests/unit/test_budget.py`
-   `tests/decision/test_models.py`
-   `tests/decision/test_constraints.py`
-   `tests/decision/test_objectives.py`
-   `tests/decision/test_baseline_ranker.py`
-   `tests/unit/test_reward_recommendation.py`

The developer reported that individual modules and the full `tests/`
suite passed. Record the exact total test count from the local pytest
summary when available; it is not stated here.

## 10. Not Yet Implemented

-   Database-backed retrieval of customer, reward, inventory, and
    campaign records.
-   Atomic budget reservation and redemption transactions.
-   Concurrency-safe inventory and budget updates.
-   Approval and redemption API endpoints.
-   Empirical calibration of ranking weights.
-   OpenJEV/Laya decision-layer integration.
-   LangGraph/MCP orchestration integration.
