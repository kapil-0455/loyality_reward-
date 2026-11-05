# User Stories and Acceptance Criteria

## US-01: Customer Behavioral Segmentation
**As a** Loyalty Marketing Manager,  
**I want to** segment registered customers based on their historical transaction patterns using RFM analytics,  
**So that** I can deliver tailored promotions aligned with customer purchasing frequency and value.

### Acceptance Criteria:
- Calculate Recency (days since last purchase), Frequency (distinct qualifying invoices), and Monetary (lifetime spend) from clean transactions.
- Segment customers using K-Means into High-Value Champions, Loyal Shoppers, At-Risk Customers, and New Buyers.
- Handle cancellations, refunds, negative quantities, and missing customer IDs deterministically.
- Expose segment attributes via API endpoint `GET /customers/{customer_id}/segments`.

---

## US-02: Inventory-Aware Reward Recommendations
**As a** Campaign Operations Manager,  
**I want to** recommend personalized rewards that deterministically check available physical inventory and campaign budget,  
**So that** customers never receive recommendations for out-of-stock items or unfunded campaigns.

### Acceptance Criteria:
- Enforce hard eligibility filters: Active account, eligible tier, sufficient points balance, active campaign.
- Enforce inventory hard barriers: `on_hand_stock - reserved_stock >= required_quantity` and `available_stock > reorder_level`.
- Enforce campaign budget limits: `budget_limit - committed_amount - approved_amount >= reward_cost`.
- If no reward satisfies all constraints, return structured status `NO_ELIGIBLE_REWARD` with explicit reason codes (`INSUFFICIENT_STOCK`, `INSUFFICIENT_POINTS`, `BUDGET_EXCEEDED`).
- Rank feasible rewards using a multi-objective scoring function and decision engine evaluation.

---

## US-03: Reward Transaction Integrity & Idempotency
**As a** System Reliability Engineer,  
**I want** duplicate redemption requests to be handled safely using idempotency keys,  
**So that** network replays and concurrent clicks cannot debit points twice or exceed budget allocations.

### Acceptance Criteria:
- Require unique `idempotency_key` string on every redemption request.
- Store redemption transactions in PostgreSQL `RewardLedger` with unique key constraint.
- Repeated requests with an identical idempotency key return the original cached response with zero additional point debits.
- Concurrent requests are serialized using PostgreSQL row-level locks (`SELECT FOR UPDATE`).

---

## US-04: Controlled Approval Workflow
**As a** Loyalty Program Administrator,  
**I want to** generate structured reward proposals that require explicit approval prior to redemption,  
**So that** automated recommendations do not bypass business controls and audit trails.

### Acceptance Criteria:
- Recommendation returns a proposal without executing points debits.
- Approval endpoint `POST /rewards/approvals` records manager/system authorization.
- Re-validate all constraints at redemption time; reject redemption if stock or budget changed between approval and redemption.

---

## US-05: Observability & Defect Troubleshooting
**As a** Platform Operations Developer,  
**I want** structured logs, request IDs, and Langfuse tracing for all agent executions,  
**So that** invalid recommendations, agent timeouts, and decision anomalies can be rapidly investigated.

### Acceptance Criteria:
- Mask sensitive credentials; log request IDs, latency, and business reason codes.
- Record all LangGraph agent node transitions and tool executions.
- Provide comprehensive automated test suite (Unit, Integration, Security, Observability) verifying 0 constraint violations.
