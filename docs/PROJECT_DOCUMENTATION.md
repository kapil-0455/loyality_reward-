# 📖 Master Project Documentation: Inventory-Aware AI Loyalty & Reward Optimisation Platform

---

## 📌 1. Executive Summary & Problem Statement

### 1.1 The Business Problem
Traditional enterprise and e-commerce customer loyalty programs suffer from four critical architectural flaws:
1. **Generic, Non-Personalized Rewards**: Customers receive one-size-fits-all discounts rather than incentives aligned with their purchasing history and engagement propensity.
2. **Stockouts & Inventory Waste**: Rewards are issued without real-time inventory checks, leading to customer frustration when redeemed items are out of stock, while slow-moving excess stock is ignored.
3. **Budget Overruns & Margin Erosion**: Marketing campaigns lack automated budget controls, leading to unprofitable campaigns where reward commitments exceed available marketing spend.
4. **AI Hallucinations & Governance Risks**: Conventional generative AI chatbots often fabricate non-existent promotions, grant unapproved points, or violate business policies when prompted by users.

### 1.2 The Solution
The **Inventory-Aware AI Loyalty & Reward Optimisation Platform** is a full-stack, enterprise-grade system that integrates:
- **Machine Learning (K-Means Clustering & RFM Analysis)** on historical transaction data.
- **A 6-Agent LangGraph State Machine** executing deterministic business policy checks alongside System-1 calibrated reward routing.
- **Model Context Protocol (FastMCP)** for standardized, auditable data retrieval.
- **Groq Cloud LLM** with rigid security guardrails for conversational customer interaction.
- **ACID-Compliant PostgreSQL** with double-spend protection (2-phase idempotent redemption).
- **Langfuse Cloud Observability** for real-time distributed tracing and telemetry.

---

## 🏗️ 2. High-Level System Architecture

The platform is designed in five decoupled tiers:

```mermaid
graph TD
    subgraph UI_Layer ["1. Presentation Layer (Streamlit Cloud)"]
        UI_Cust["👤 Customer Portal\n• Perks & Balance\n• 1-Click Redeem\n• 🤖 AI Concierge Speech Box"]
        UI_Admin["⚙️ Admin Portal\n• RFM Cluster Charts\n• Real-Time Stock Barriers\n• Campaign Budgets\n• Langfuse Trace Inspector"]
    end

    subgraph API_Layer ["2. API & Backend Service (FastAPI on Render Docker)"]
        API_Route["⚡ REST Endpoints\n• /rewards/agentic-recommendations\n• /rewards/recommendations\n• /rewards/approvals\n• /rewards/redemptions\n• /customers/{id}/profile"]
        API_Sec["🔒 Security Middleware\n• Bearer Token Authentication\n• Request ID Tracking\n• CORS Middleware"]
    end

    subgraph Agentic_Layer ["3. Multi-Agent Orchestration (LangGraph 6-Node Graph)"]
        A1["🧭 Agent 1: Router Agent\n(Intent & Prompt Guardrails)"]
        A2["🌐 Agent 2: Data Agent\n(FastMCP Client)"]
        A3["📊 Agent 3: Analytics Agent\n(RFM & K-Means Clusters)"]
        A4["🛡️ Agent 4: Eligibility Agent\n(Hard Constraints Engine)"]
        A5["🏆 Agent 5: Reward Agent\n(Multi-Objective + Laya Router)"]
        A6["💬 Agent 6: Response Agent\n(Groq LLM Synthesis)"]

        A1 --> A2 --> A3 --> A4 --> A5 --> A6
    end

    subgraph Protocol_Layer ["4. Protocols & Tools (FastMCP Layer)"]
        MCP["🔌 LoyaltyMCP Server\n• get_customer_profile\n• get_active_rewards\n• get_product_inventory\n• get_campaign_details\n• get_transaction_history"]
    end

    subgraph Data_Layer ["5. Persistence & Observability"]
        DB[(🐘 Supabase PostgreSQL\n• Profiles • Inventory\n• Budgets • Ledger)]
        LF["🛰️ Langfuse Cloud\n• Trace Spans • Latency (ms)\n• Token Costs • Audit"]
    end

    UI_Cust & UI_Admin --> API_Route
    API_Route --> Agentic_Layer
    A2 <--> MCP
    MCP <--> DB
    Agentic_Layer -.-> LF
```

---

## 🔬 3. Machine Learning & Behavioral Intelligence Pipeline

The analytical core was developed through Jupyter Notebooks (`notebooks/01` to `06`) using the **UCI Online Retail II dataset** (500,000+ real transactions):

```
[Raw Excel Dataset] ➔ 02_Data_Cleaning ➔ 03_EDA ➔ 04_RFM_Features ➔ 05_KMeans_Clustering ➔ Database Seeding
```

### 3.1 Data Cleaning & Preprocessing (`02_data_cleaning_complete.ipynb`)
- **Negative & Return Removal**: Invoices starting with 'C' (cancellations) and negative quantity records were isolated.
- **Customer ID Imputation**: Records with missing customer IDs were filtered from RFM calculations.
- **Line Amount Calculation**: Computed as `quantity * price` per SKU item.

### 3.2 RFM Feature Engineering (`04_rfm_feature_engineering.ipynb`)
For every unique customer, three behavioral dimensions were calculated:
1. **Recency ($R$)**: Days elapsed between the customer's last invoice and the reference cutoff date.
2. **Frequency ($F$)**: Total distinct purchase transactions placed by the customer.
3. **Monetary Value ($M$)**: Total cumulative lifetime expenditure (LTV) in dollars.

### 3.3 K-Means Customer Segmentation (`05_kmeans_customer_segmentation.ipynb`)
- **Feature Transformation**: Applied `StandardScaler` after log-transforming skewed monetary and frequency metrics.
- **Optimal $K$ Selection**: Evaluated using **Elbow Curves (Inertia)** and **Silhouette Coefficient Analysis** ($K=2$ to $5$).
- **Segment Definition**:
  - **Cluster 1 — High-Value Champions**: High Frequency, high Monetary spend ($>\$6,500$ LTV), low Recency.
  - **Cluster 0 — At-Risk / Occasional Shoppers**: Low Frequency, moderate/low spend ($\sim\$611$ LTV), higher Recency.
- The resulting tables (`customer_rfm_segments` and `rfm_customer_features`) were uploaded directly to PostgreSQL.

---

## 🤖 4. Multi-Agent AI Architecture (LangGraph 6-Node Graph)

Instead of relying on a single monolithic prompt, the system breaks decisions into six modular, specialized agents connected via a LangGraph state machine:

| Agent Node | Function & Responsibilities | Key Technologies |
|---|---|---|
| **1. Router Agent** | Validates user intent (`REWARD_RECOMMENDATION` vs `UNKNOWN`). Enforces role boundaries and strips prompt-injection attempts. | Regex, deterministic pattern matching |
| **2. Data Agent** | Fetches required customer attributes, active reward catalog, inventory stock levels, and campaign budgets. | FastMCP Client protocol |
| **3. Analytics Agent** | Enriches customer state with RFM scores, lifetime spending, and K-Means behavioral cluster assignment. | PostgreSQL ORM + scikit-learn models |
| **4. Eligibility Agent** | **Zero-Hallucination Policy Gate**: Checks points balance ($pts \ge req$), loyalty tier compatibility, inventory stock ($stock > 0$), and campaign budget remaining. | Deterministic rule engine |
| **5. Reward Agent** | Computes multi-objective reward ranking using: $$\text{Score} = w_1 \cdot \text{Rel} + w_2 \cdot \text{Val} + w_3 \cdot \text{Inv} - w_4 \cdot \text{Cost}$$ Integrates **Laya System-1 Calibrated Router** with automated fallback to baseline ranking. | Laya, PyTorch (CPU), NumPy |
| **6. Response Agent** | Translates structured decision outputs into a personalized, friendly, customer-facing natural language response. | Groq Cloud LLM (`openai/gpt-oss-120b`) |

---

## 🔒 5. Financial Security & Double-Spend Protection

To guarantee financial integrity across concurrent transactions, reward redemptions execute through a **2-Phase Idempotent Protocol**:

```mermaid
sequenceDiagram
    autonumber
    actor Customer as 👤 Customer / Client
    participant API as ⚡ FastAPI Backend
    participant DB as 🐘 PostgreSQL Database
    participant Ledger as 📜 Reward Ledger

    Note over Customer,Ledger: Phase 1: Pre-Approval & Constraint Lock
    Customer->>API: POST /rewards/approvals (reward_id, purchase_value, idempotency_key)
    API->>DB: Check Points, Stock & Budget with Row-Level Lock (SELECT FOR UPDATE)
    DB-->>API: Validated (points available, stock reserved)
    API->>DB: INSERT into reward_approvals (status='APPROVED', token_expires_in=15m)
    API-->>Customer: Return approval_id & approval_token

    Note over Customer,Ledger: Phase 2: Atomic Redemption & Debit
    Customer->>API: POST /rewards/redemptions (approval_id, idempotency_key)
    API->>DB: Atomic Transaction Begin
    API->>DB: Debit customer_loyalty_profiles.points_balance
    API->>DB: Decrement inventory_snapshots.current_stock
    API->>DB: Update campaign_budgets.committed_spend
    API->>Ledger: INSERT into reward_ledger (immutable audit record)
    API->>DB: Commit Transaction
    API-->>Customer: Return redemption_id (HTTP 200 OK)
```

- **Fail-Closed Security**: Any validation error, expired token, or duplicate idempotency key aborts the transaction immediately without debiting points.
- **Idempotency Guarantee**: If a network glitch causes the client to send the redemption request twice, the system detects the existing `idempotency_key` and returns the previous successful result without double-debiting.

---

## 🛰️ 6. Observability & Distributed Tracing (Langfuse)

The entire multi-agent lifecycle is monitored via **Langfuse Cloud (OpenTelemetry standard)**:
- **Per-Agent Latency Tracking**:
  - Router Agent: $\sim 28\text{ ms}$
  - Data Retrieval via FastMCP: $\sim 42\text{ ms}$
  - Analytics & K-Means: $\sim 31\text{ ms}$
  - Eligibility Policy Gate: $\sim 18\text{ ms}$
  - Reward Optimization: $\sim 35\text{ ms}$
  - Response Agent (Groq LLM): $\sim 1.2\text{ s}$
- **Trace Spans**: Every decision includes execution traces containing input state, output payload, and failure codes.
- **Audit Logs**: Stored immutably for compliance and model performance evaluations.

---

## 🖥️ 7. Full-Stack User Interfaces (Streamlit)

### 7.1 Customer Portal (`👤 Customer Dashboard`)
- **Overview (Home)**: Points Balance card, Loyalty Tier badge, recommended reward cards with 1-click redemption.
- **My Rewards**: Filtered catalog displaying all unlocked privileges for the customer's tier.
- **⚡ Redeem Reward**: Cart value and date evaluation with real-time stock assurance.
- **🤖 AI Loyalty Concierge**:
  - **Live 6-Node Visual Stepper**: Progress indicators for all 6 agents.
  - **Groq LLM Speech Box**: Conversational, personalized natural language message.
  - **Deep State Inspector**: Collapsible JSON tree showing step-by-step state mutations.
- **Points & History**: Ledger debit history and approval proposals audit table.
- **Profile**: Account status and customer RFM analytics metrics ($R$, $F$, $M$ and cluster name).

### 7.2 Admin Command Center (`⚙️ Admin Dashboard`)
- **Operations Overview**: Active customers count, total rewards, active marketing campaigns, segmentation donut chart, top redemptions bar chart.
- **Customer Directory**: Searchable table with tier and points balance inspection.
- **Reward & Inventory Management**: Live inventory tracking with safety threshold alerts.
- **Campaign Budgets**: Committed vs remaining budget trackers preventing campaign overruns.
- **Model Monitoring & Observability**: Real-time agent status table, Laya confidence gates, and live Langfuse trace generator.

---

## ☁️ 8. Cloud Deployment Topology

The system is deployed on a modern, decoupled cloud architecture:

| Component | Platform | Configuration |
|---|---|---|
| **Frontend UI** | **Streamlit Community Cloud** | Python 3.11+, Auto-deployed from GitHub `main` |
| **Backend REST API** | **Render.com (Docker)** | Containerized Linux build (`Dockerfile`), dynamic `$PORT`, keep-alive 300s |
| **Database** | **Supabase Cloud / Neon** | PostgreSQL 16 with SSL, connection pooling, ACID transaction guarantees |
| **LLM Inference** | **Groq Cloud API** | Fast inference engine (`openai/gpt-oss-120b`) |
| **Observability** | **Langfuse Cloud** | Distributed telemetry, span analytics, latency tracking |

### Environment Variables Reference
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
GROQ_API_KEY=gsk_...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
ENVIRONMENT=production
PORT=8000
```

---

## 🧪 9. Quality Assurance & Test Suite

The project includes an extensive automated test suite executed with `pytest`:
- **Unit Tests**:
  - Individual agent functions (`test_router_agent.py`, `test_analytics_agent.py`, `test_eligibility_agent.py`, `test_response_agent.py`).
  - Constraint checks (`test_constraints.py`, `test_objectives.py`, `test_models.py`).
- **Integration Tests**:
  - Full LangGraph execution (`test_graph_builder.py`, `test_graph_runner.py`).
  - FastMCP tool calling (`test_data_agent_mcp.py`, `test_mcp_client.py`).
  - 2-Phase redemption idempotency (`test_repositories.py`).
- **Results**: **111+ tests passing** with zero security or policy violations.

---

## 🎓 10. Viva / Interview Questions & Answers

### Q1: What makes your system "inventory-aware"?
> **Answer**: Most loyalty recommenders only check customer points. Our system enforces an **Eligibility Agent (Hard Constraint Gate)** that queries live inventory snapshots through MCP. If stock is zero or below the reserved safety threshold, the reward is pruned immediately *before* ranking or LLM generation.

### Q2: Why did you use LangGraph instead of a simple LangChain prompt chain?
> **Answer**: Reward recommendations require conditional routing, multi-step state persistence, and deterministic policy enforcement. LangGraph provides a cyclical state machine where agents run as isolated nodes with explicit inputs/outputs. If an eligibility constraint fails, conditional edges gracefully bypass subsequent agents without executing costly LLM calls.

### Q3: How do you prevent double-spending of loyalty points?
> **Answer**: We implemented a **2-Phase Idempotent Protocol**. First, `approve_reward` validates points and generates a time-bound approval token. Second, `redeem_reward` executes an atomic database transaction with row-level locks (`SELECT FOR UPDATE`) and logs an immutable ledger entry indexed by a unique `idempotency_key`.

### Q4: How is LLM hallucination prevented?
> **Answer**: The LLM (Agent 6) is strictly a **presentation layer**, not a decision maker. The decision of which rewards are feasible is made deterministically by Agents 3, 4, and 5. The LLM only receives verified facts in its system prompt and operates under strict guardrails forbidding it from inventing reward details or overriding policy.
