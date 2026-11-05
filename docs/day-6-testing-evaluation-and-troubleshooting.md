# Day 6 — Testing, Evaluation and Troubleshooting

**Project:** Loyalty and Reward Optimisation with Inventory-Aware Rewards  
**Sprint phase:** Day 6 of the 7-Day Agentic AI Project Sprint  
**Branch:** `day6-testing-evaluation`  
**Status:** Implementation and regression tests committed; post-patch local execution is pending.

## 1. Day 6 Objective

Day 6 verifies correctness, security, reliability and business relevance. This report separates test evidence already produced on the previous project revision from regression tests added on this branch. A test is not described as passing until it has actually been executed.

## 2. Test Execution Evidence

The project owner previously ran the complete test suite on the pre-Day-6-fix revision:

- **126 passed**
- **Duration:** 213.37 seconds
- The two PostgreSQL concurrency tests passed after configuring `TEST_DATABASE_URL` with a valid test database connection.
- The suite included API, agent, decision, MCP, unit and integration tests.

The project owner also reported that the expanded local Laya adapter test file passed 9 tests. That local version was not present on the GitHub main branch at the time this branch was created; the adapter tests have therefore been consolidated and expanded on this branch.

**Important:** The 126-pass result is historical evidence for the previous revision. Re-run the suite on this branch before marking the updated code as fully verified.

## 3. Business Rule and Edge-Case Coverage

Existing tests cover:

- Insufficient customer points and ineligible loyalty tier.
- Expired rewards and minimum-purchase requirements.
- Insufficient inventory and replenishment constraints.
- Insufficient campaign budget and inactive campaigns.
- Missing policy results and rejection of infeasible candidates.
- Empty candidate lists and invalid candidate exclusion.
- Approval/redemption workflow integration.
- Concurrent approval and concurrent redemption with PostgreSQL.

Relevant test locations include:

- `tests/unit/test_eligibility.py`
- `tests/unit/test_inventory.py`
- `tests/unit/test_budget.py`
- `tests/decision/test_constraints.py`
- `tests/decision/test_baseline_ranker.py`
- `tests/integration/test_redemption_flow.py`
- `tests/integration/test_concurrent_approval.py`
- `tests/integration/test_concurrent_redemption.py`

## 4. Defect Investigation and Fixes

### Defect 1 — NaN values could pass reward objective validation

**Reproduction:** Pass `float("nan")` as an objective input to `calculate_reward_score()`.

**Root cause:** The previous range check only tested `value < 0 or value > 100`. Both comparisons are false for NaN, so NaN could enter the weighted score and produce a non-finite ranking score.

**Fix:** `backend/app/decision/objectives.py` now rejects non-finite values using `math.isfinite()`, in addition to enforcing the inclusive 0–100 range.

**Regression coverage:** `tests/decision/test_objectives.py` tests NaN, positive infinity and negative infinity.

### Defect 2 — NaN or out-of-range Laya confidence could bypass the confidence gate

**Reproduction:** Return a valid reward ID with `answer_confidence=float("nan")` from the mocked Laya response.

**Root cause:** The previous adapter only checked `confidence < MIN_CONFIDENCE`. A NaN comparison returns false, so the invalid confidence could bypass the 0.60 threshold. Values outside the probability range could also be accepted if they were greater than the threshold.

**Fix:** `backend/app/decision/laya_adapter.py` now requires confidence to be finite and within [0, 1] before applying the 0.60 minimum. Invalid values enter the existing deterministic baseline fallback path.

**Regression coverage:** `tests/decision/test_laya_adapter.py` tests NaN, infinity, out-of-range values, exact-threshold acceptance, malformed responses, ineligible candidate filtering and empty feasible sets.

## 5. Laya vs Deterministic Baseline Evaluation

An eight-scenario synthetic comparison was run using the same candidate sets for the baseline and Laya.

| Measure | Observed result |
|---|---:|
| Scenarios | 8 |
| Raw Laya output valid candidate ID | 8/8 (100%) |
| Raw Laya vs baseline top-choice agreement | 2/8 (25%) |
| Laya choices accepted by adapter at 0.60 threshold | 0/8 (0%) |
| Adapter baseline fallback | 8/8 (100%) |

The raw Laya/baseline agreement is **not accuracy**. There is no labelled ground-truth dataset of customer reward preferences or actual redemptions in this evaluation. Because all eight outputs fell below the configured confidence threshold, the final adapter selections came from the deterministic baseline.

The adapter's 0.60 threshold is a configured safety gate, not a statistically validated production threshold.

### Laya checkpoint temperature warning

The installed Laya checkpoint reported an invalid raw temperature for the `choice:11+` bucket (approximately 0.1006), which the package clamps to 0.5. The package's bucket mapping assigns 3–5 choices to `choice:3-5`; the reward comparison used three candidates. Therefore, the warning for `choice:11+` does not by itself establish that the three-candidate bucket is affected. The active 3–5 bucket calibration and empirical calibration on labelled reward outcomes remain unverified.

## 6. Security Test Evidence and Gaps

Existing tests verify that:

- The Data Agent cannot invoke approval or redemption through its MCP allowlist.
- Unexpected MCP arguments are rejected before calling the tool.
- The response prompt includes instructions to treat retrieved content as untrusted, not follow embedded instructions, not reveal system prompts, and not modify points.

Relevant test: `tests/agents/test_security_guardrails.py`.

**Not fully verified by the current automated suite:**

- Application-wide authentication and authorisation on every approval/redemption API route.
- A complete prompt-injection attack matrix against every agent/tool boundary.
- Dedicated sensitive-data leakage tests across all API and log outputs.
- Invalid approval and approval-tampering cases as a separate security test group.

The agent tool restrictions do not replace API-level authentication and authorisation. These are recorded as security limitations, not claimed as completed controls.

## 7. Known Limitations

1. The synthetic Laya evaluation has no labelled preference/redemption ground truth; it cannot establish recommendation accuracy.
2. All eight Laya decisions were rejected by the configured confidence threshold, so the evaluated final selections used the baseline.
3. The checkpoint temperature warning concerns `choice:11+`; the active `choice:3-5` bucket still needs direct calibration verification.
4. Application-wide API authentication/authorisation requires independent verification.
5. The full test suite must be rerun after the Day 6 regression fixes are pulled locally.
6. PostgreSQL concurrency tests require a valid `TEST_DATABASE_URL`; do not point it at a production database.

## 8. Reproduction Commands

Run from the repository root after checking out this branch:

```powershell
python -m pytest tests/decision/test_objectives.py tests/decision/test_laya_adapter.py -v
python -m pytest -v
```

For the PostgreSQL concurrency tests, configure `TEST_DATABASE_URL` in the local PowerShell session with a dedicated test database before running the full suite. Never commit database credentials or paste them into logs.

## 9. Day 6 Completion Checklist

- [x] Existing full suite executed: 126 passed on the previous revision.
- [x] Business-rule, expiry, points, stock, replenishment and budget test coverage reviewed.
- [x] Eight-scenario Laya/baseline comparison recorded with limitations.
- [x] Two concrete defects investigated and fixes committed.
- [x] Regression tests added for both defects.
- [x] Existing MCP guardrail tests and their scope documented.
- [ ] Re-run targeted regression tests on this branch.
- [ ] Re-run the full suite on this branch.
- [ ] Expand dedicated API authentication, invalid-approval and sensitive-data security tests.

Day 6 implementation is committed for review. Mark Day 6 fully Done only after the pending test runs and remaining security checks have been addressed or explicitly accepted as project limitations.
