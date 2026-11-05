# Decision Layer Evaluation: Laya vs Deterministic Baseline

## 1. Overview
The recommendation system separates **deterministic constraint enforcement** from **multi-objective decision optimization**:
- **Deterministic Hard Constraints:** Only rewards that satisfy all customer eligibility, points, tier, stock availability, and campaign budget rules are admitted into the feasible set.
- **Decision Engine (Laya vs Baseline):** Feasible alternatives are evaluated to select the candidate that best balances customer relevance, reward value, gross margin, and inventory depletion.

---

## 2. Deterministic Baseline Ranker
The deterministic baseline computes an objective score for each candidate $c$ using a documented weighted utility function:

$$\text{Score}(c) = w_1 \cdot \text{Relevance} + w_2 \cdot \text{RewardValue} + w_3 \cdot \text{InventorySuitability} - w_4 \cdot \text{CostPenalty}$$

- Standardized weights: $w_1 = 0.35, w_2 = 0.25, w_3 = 0.25, w_4 = 0.15$.
- Normalized inputs: All sub-scores bounded in $[0.0, 1.0]$.
- Robustness: Handles NaN, positive infinity, and negative infinity inputs safely without crashing.

---

## 3. Laya Model Integration & Confidence Gate
- **Adapter:** Implemented in `backend/app/decision/laya_adapter.py`.
- **Confidence Gate:** Enforces a strict confidence threshold of **0.60**.
  - If Laya returns confidence $\ge 0.60$ and the selected reward is in the feasible set, Laya's choice is accepted.
  - If Laya returns confidence $< 0.60$, returns an unknown candidate ID, or times out, the system safely falls back to the deterministic baseline ranker.

---

## 4. Evaluation Across Synthetic Business Scenarios
The decision layer was benchmarked across 8 synthetic evaluation scenarios:

| Scenario | Objective Goal | Raw Laya Choice | Baseline Choice | Laya Conf | Gate $\ge 0.60$ | Final Action | Constraint Adherence |
|---|---|---|---|---|---|---|---|
| 1: High Points / Gold | Customer Satisfaction | SYN-REWARD-001 | SYN-REWARD-001 | 0.42 | ❌ Rejected | Fallback (Baseline) | 100% Eligible |
| 2: Low Stock Alternative | Stock Depletion Risk | SYN-REWARD-004 | SYN-REWARD-002 | 0.38 | ❌ Rejected | Fallback (Baseline) | 100% In-Stock |
| 3: Budget Constraint | Budget Preservation | SYN-REWARD-001 | SYN-REWARD-005 | 0.51 | ❌ Rejected | Fallback (Baseline) | 100% Within Budget |
| 4: High Margin Goal | Retail Profitability | SYN-REWARD-003 | SYN-REWARD-003 | 0.49 | ❌ Rejected | Fallback (Baseline) | 100% Eligible |
| 5: Churn Prevention | Retention Incentive | SYN-REWARD-006 | SYN-REWARD-006 | 0.45 | ❌ Rejected | Fallback (Baseline) | 100% Eligible |
| 6: Minimum Stock Edge | Reorder Threshold | SYN-REWARD-002 | SYN-REWARD-001 | 0.39 | ❌ Rejected | Fallback (Baseline) | 100% In-Stock |
| 7: Multi-Candidate Set | Tier Hierarchy | SYN-REWARD-005 | SYN-REWARD-005 | 0.52 | ❌ Rejected | Fallback (Baseline) | 100% Eligible |
| 8: Expiring Campaign | Spend Clearance | SYN-REWARD-001 | SYN-REWARD-003 | 0.44 | ❌ Rejected | Fallback (Baseline) | 100% Active Campaign |

### Key Findings & Metrics
1. **Constraint Violation Rate:** **0.0%** — Neither model is permitted to bypass physical inventory or budget limits.
2. **Mean Laya Confidence:** **0.45** (Below the 0.60 calibration threshold).
3. **Safety Fallback Execution:** **100%** successful failover to the deterministic baseline.
4. **Conclusion:** While Laya proposes reasonable candidates, its confidence is uncalibrated ($\le 0.52$). The fail-closed architecture guarantees that business safety constraints remain uncompromised at all times.

