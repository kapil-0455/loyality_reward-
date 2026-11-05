# Business Problem Statement

## 1. Context & Business Domain
Modern retail and e-commerce enterprises rely heavily on customer loyalty programs, vouchers, discounts, and personalized rewards to foster customer retention and drive lifetime purchase value (LTV). However, conventional loyalty reward mechanisms suffer from significant operational inefficiencies:

1. **Disconnected Targeting & Margin Erosion:** Inactive or churning customers often receive the same high-value promotions as active VIP champions, wasting marketing budget and eroding gross margin without driving incremental transactions.
2. **Stock-Blind Recommendations:** Recommendation engines frequently suggest items without validating live on-hand physical stock, resulting in orders placed on depleted inventory and fulfilment backlogs.
3. **Uncontrolled Budget Commitments:** Marketing campaigns routinely breach seasonal spend limits because redemptions are evaluated without real-time committed vs approved budget accounting.
4. **Duplicate Debits & Concurrency Leaks:** Without strict idempotency keys and row-level database locks, network retries and concurrent redemption clicks create duplicate point deductions and double-reward allocations.
5. **Black-Box AI Decisions:** Machine learning decision models frequently recommend attractive but commercially infeasible rewards without deterministic constraint enforcement or explainable reason codes.

---

## 2. Project Objectives
The objective of this project is to build an **Inventory-Aware Reward Optimisation and Recommendation System** that bridges customer behavioural analytics, deterministic policy guardrails, and agentic decision orchestration:

- **Customer Behavioral Analytics:** Ingest UCI Online Retail II transactional data and construct Recency, Frequency, and Monetary (RFM) behavioural features clustered via K-Means segmentation.
- **Deterministic Policy Engine:** Enforce non-negotiable business guardrails—points sufficiency, tier eligibility, reward validity/expiry, live inventory replenishment rules, and campaign budget barriers.
- **Multi-Objective Optimization & Decision Support:** Rank feasible candidates by balancing customer relevance, reward value, gross margin, and stock depletion penalties, evaluated via Laya with deterministic fallback.
- **Agentic Workflow Orchestration:** Coordinate request routing, MCP data retrieval, RFM computation, constraint validation, and proposal generation via a 6-node LangGraph state machine.
- **Transactional Integrity:** Provide atomic point deduction, budget commitments, and duplicate prevention via PostgreSQL row-level locks and idempotency keys.
- **Enterprise Visual Portals:** Deliver dedicated Customer and Admin portals via Streamlit connected to real-time Neon PostgreSQL databases.
