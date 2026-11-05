# Day 6 — Testing, Evaluation and Troubleshooting

**Project:** Loyalty and Reward Optimisation with Inventory-Aware Rewards  
**Sprint phase:** Day 6 of the 7-Day Agentic AI Project Sprint  
**Branch:** `day6-testing-evaluation`  
**Status:** All Day 6 testing, security validation, observability, rollback, and regression suites passed.

## 1. Day 6 Objective

Day 6 verifies correctness, security, reliability, observability, and business relevance across all layers:
1. Business rules and edge-case validation (points, tiers, expiry, stock, budgets).
2. Approval and redemption workflows (integration, idempotency, concurrency).
3. Defect fixes and objective/confidence boundary tests.
4. Laya evaluation vs deterministic baseline under configured thresholds.
5. API authentication on sensitive routes (bearer-token fail-closed gate).
6. Invalid approval and request tampering testing.
7. Sensitive data leakage prevention across APIs and logs.
8. Prompt injection and tool abuse testing across agents and MCP boundaries.
9. Langfuse observability and trace execution verification.
10. Structured logging, latency metrics, and `X-Request-ID` correlation middleware.
11. Database rollback and transactional consistency under failure.

## 2. Test Execution Evidence

### Full Regression Suite
- **Base Full Suite Execution:** **146 passed** in 243.26s (~4 minutes).
- **Post-Day-6 Additions:** **28 new tests added**, bringing total test suite to **175 tests**.
- **Final Full Suite Execution:** **175 passed** (verified after adding the redemption idempotency payload-tampering regression test).
- **Targeted Security & Observability Suite:** **37 passed** in 5.96s:
  - `tests/security/test_invalid_approvals.py`: 8 passed
  - `tests/security/test_prompt_injection.py`: 5 passed
  - `tests/security/test_sensitive_api_auth.py`: 9 passed
  - `tests/security/test_sensitive_data_leakage.py`: 4 passed
  - `tests/observability/test_langfuse_tracing.py`: 4 passed
  - `tests/observability/test_structured_logging.py`: 4 passed
  - `tests/integration/test_db_rollback.py`: 3 passed

## 3. Business Rule and Edge-Case Coverage

Tests systematically verify all core business invariants:
- **Eligibility:** Inactive customers, insufficient customer points, ineligible customer loyalty tier, expired rewards, and sub-minimum purchase values are rejected with explicit reason codes (`tests/unit/test_eligibility.py`).
- **Inventory Hard Constraints:** Insufficient on-hand stock and replenishment lead-time constraints block infeasible reward candidates (`tests/unit/test_inventory.py`).
- **Campaign Budgeting:** Inactive campaigns and exhausted campaign budgets reject allocations (`tests/unit/test_budget.py`).
- **Approval & Redemption Integration:** End-to-end reserve -> approve -> redeem workflow with customer points debit and inventory deduction (`tests/integration/test_redemption_flow.py`).
- **Concurrency & Idempotency:** Concurrent approvals and redemptions tested under row locking (`SELECT FOR UPDATE`), guaranteeing zero over-commit and zero double-redemption (`tests/integration/test_concurrent_approval.py`, `tests/integration/test_concurrent_redemption.py`).

## 4. Defect Investigation and Fixes

### Defect 1 — NaN values could pass reward objective validation
- **Reproduction:** Pass `float("nan")` as an objective input to `calculate_reward_score()`.
- **Root cause:** The previous range check only tested `value < 0 or value > 100`. Both comparisons evaluate to `False` for `NaN`, allowing non-finite numbers to corrupt ranking scores.
- **Fix:** `backend/app/decision/objectives.py` enforces finite numbers using `math.isfinite()` along with the inclusive 0–100 boundary.
- **Regression coverage:** `tests/decision/test_objectives.py` tests `NaN`, positive infinity (`+inf`), and negative infinity (`-inf`).

### Defect 2 — NaN or out-of-range Laya confidence could bypass confidence gate
- **Reproduction:** Return a valid candidate ID with `answer_confidence=float("nan")` from the Laya response.
- **Root cause:** Checking `confidence < MIN_CONFIDENCE` evaluates to `False` for `NaN`, bypassing the 0.60 safety threshold.
- **Fix:** `backend/app/decision/laya_adapter.py` validates that confidence is finite and within $[0.0, 1.0]$ before evaluating against the 0.60 threshold. Non-finite or out-of-range values safely trigger the deterministic baseline fallback.
- **Regression coverage:** `tests/decision/test_laya_adapter.py` tests `NaN`, `+inf`, out-of-range probabilities, exact threshold bounds, and malformed inputs.

## 5. Laya vs Deterministic Baseline Evaluation

An 8-scenario synthetic comparison was evaluated using identical candidate sets:

| Measure | Observed Result |
|---|---:|
| Total Scenarios | 8 |
| Raw Laya Valid Candidate ID | 8/8 (100%) |
| Raw Laya vs Baseline Top-Choice Agreement | 2/8 (25%) |
| Laya Choices Accepted at $\ge 0.60$ Threshold | 0/8 (0%) |
| Deterministic Baseline Fallback Invocations | 8/8 (100%) |

**Evaluation Notes:**
- Raw agreement with baseline does **not** equal recommendation accuracy; no ground-truth customer preference dataset was available.
- The 0.60 threshold acted as an effective safety gate, defaulting to deterministic scoring whenever model confidence was insufficient.
- The installed Laya checkpoint reported an invalid raw temperature for the `choice:11+` bucket, which was clamped to 0.5. Active 3–5 choice calibration remains unverified empirically against customer conversion.

## 6. Security Testing & Guardrails

### 6.1 Authentication Protection
- `backend/app/api/security.py` implements a fail-closed HTTP Bearer token dependency (`require_campaign_manager`).
- Protected routes:
  - `POST /rewards/approvals`
  - `POST /rewards/redemptions`
  - `GET /rewards/redemptions/{redemption_id}`
- Reject missing token (401), invalid token (401), and unconfigured server token (503).
- Regression suite: `tests/security/test_sensitive_api_auth.py`.

### 6.2 Invalid Approvals and Request Tampering
- `tests/security/test_invalid_approvals.py` verifies:
  1. Rejected approval (`approved=False`): Status stored as `REJECTED`; zero budget and zero stock reserved.
  2. Blocked redemption of rejected approval: Attempts fail with 400 (`Approval is not available for redemption`).
  3. Approval idempotency tampering: Re-using an idempotency key with modified payload raises 400.
  4. Redemption tampering: Customer ID, reward ID, or campaign ID mismatch against the approval raises 400 (`Request does not match approval`).
  5. Double redemption prevention: Re-redeeming an already redeemed approval with a new key is blocked.
  6. Reward-campaign mismatch: Disallowed cross-campaign allocations are rejected.

### 6.3 Sensitive Data Leakage Prevention
- `tests/security/test_sensitive_data_leakage.py` verifies:
  1. Internal 500 exceptions in approval/redemption routes return generic sanitized messages and never disclose database URLs, credentials, or stack traces.
  2. Public `/health` and status endpoints never expose environment variables or secret keys.
  3. Authentication 401 challenges never reveal the expected token value.
  4. Structured logging filters and masks sensitive keys (`Authorization`, `password`, `secret`, `api_key`).

### 6.4 Prompt Injection & Tool Guardrails
- `tests/security/test_prompt_injection.py` and `tests/agents/test_security_guardrails.py` verify:
  1. Data Agent strictly enforces an allowed tool whitelist (`customer`, `transactions`, `inventory`, `campaign`, `reward`, `reward_mappings`, `active_rewards`); requests for `drop_table`, `eval`, or SQL injection return `INVALID_REQUEST`.
  2. Strict parameter schema enforcement rejects unexpected arguments.
  3. Response Agent prompt embeds explicit security instructions: treat retrieved context as untrusted input, never follow embedded instructions, never modify points/budget/inventory, and never reveal system prompts.
  4. Router Agent prevents role spoofing: user role is taken exclusively from authenticated session data, blocking prompt attempts to escalate privileges.

## 7. Observability & Logging

### 7.1 Langfuse Tracing
- `backend/app/observability/tracer.py` integrates agent execution and tool span tracing.
- Captures `trace_id`, `agent_name`, input states, output states, execution latency, and error states.
- Fails open gracefully in development/testing when `LANGFUSE_PUBLIC_KEY` is unset.
- Verified in `tests/observability/test_langfuse_tracing.py`.

### 7.2 Structured JSON Logging & Request ID Middleware
- `backend/app/observability/logging.py` introduces:
  - `RequestIDLoggingMiddleware`: Injects or propagates `X-Request-ID` across all HTTP responses.
  - Latency measurement (`latency_ms`) and outcome categorization (`SUCCESS`, `CLIENT_ERROR`, `SERVER_ERROR`).
  - `StructuredJsonFormatter`: Formats logs into structured JSON containing timestamps, log level, request IDs, and performance metrics.
  - `mask_sensitive_dict`: Sanitizes headers and bodies to prevent bearer token leakage in log sinks.
- Verified in `tests/observability/test_structured_logging.py`.

## 8. Database Rollback and Consistency

- `tests/integration/test_db_rollback.py` verifies atomic transactions:
  1. When approval fails business validation (e.g. minimum purchase not met), database session rolls back: no approval record persists, and campaign budgets / inventory reservations remain untouched.
  2. If an unexpected commit error occurs during approval, rollback cleans up state.
  3. If redemption fails mid-transaction (e.g. points debit failure or database error), rollback ensures points are not deducted, inventory on hand remains unchanged, and approval status remains `APPROVED` rather than corrupting to `REDEEMED`.

## 9. Known Security & Architecture Limitations

1. **Shared Bearer Token (MVP Auth):** The current implementation uses a single shared `CAMPAIGN_MANAGER_API_TOKEN`. It does not support individual manager identities, fine-grained RBAC, per-campaign object permissions, or automated token rotation.
2. **Laya Calibration Ground Truth:** Synthetic comparisons cannot substitute for empirical customer redemption logs. The 0.60 confidence threshold is a defensive heuristic, not a statistically validated cutoff.
3. **LLM Non-Determinism:** While the prompt enforces strict guardrails, defense-in-depth relies on downstream code logic (deterministic baseline ranker and schema validation), which should never trust LLM output for database mutations.

## 10. Reproduction Commands

From project root:

```powershell
# Run Day 6 Security, Observability and Rollback Suite
python -m pytest tests/security/ tests/observability/ tests/integration/test_db_rollback.py -v

# Run Targeted Regression Suite (Objectives, Laya, Auth, Guards)
python -m pytest tests/decision/test_objectives.py tests/decision/test_laya_adapter.py tests/security/ -v

# Run Full Pytest Suite
python -m pytest -v
```

## 11. Day 6 Completion Checklist

- [x] Full regression suite executed on latest revision: **175 passed**.
- [x] Business-rule, expiry, points, stock, replenishment, and budget coverage verified.
- [x] Eight-scenario Laya vs baseline comparison recorded with documented limitations.
- [x] Defects 1 (NaN in objectives) & 2 (NaN in Laya confidence) resolved and covered.
- [x] Dedicated API authentication on sensitive routes implemented and tested.
- [x] Invalid approval, rejected status, and request tampering suite added and passed.
- [x] Sensitive data leakage prevention verified across 500 error responses and logs.
- [x] Prompt injection and agent tool privilege escalation tests implemented and passed.
- [x] Langfuse trace logging module implemented and verified.
- [x] Structured JSON logging, latency metrics, and `X-Request-ID` middleware implemented.
- [x] Database rollback and consistency under failure verified.
- [x] Day 6 documentation, limitations, and sign-off report finalized.
