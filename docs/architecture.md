# System Architecture & Technical Specifications

## 1. High-Level System Architecture Diagram
```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│            SYSTEM ARCHITECTURE (Streamlit UIs + Agentic Orchestration with LangGraph + MCP)    │
└────────────────────────────────────────────────────────────────────────────────────────────────┘

 ┌────────────────────────────────┐                 ┌───────────────────────────────┐
 │   Customer Dashboard (UI)      │    HTTP (JSON)  │     Backend API (FastAPI)     │
 │ • Home & Metrics (Points, Tier)│ ──────────────> │ • /recommend                  │
 │ • Recommended Rewards Cards    │                 │ • /redeem                     │
 │ • Recent Transactions Table    │                 │ • /inventory                  │
 └────────────────────────────────┘                 │ • Pydantic Validation         │
                                                    │ • Bearer Token Authentication │
 ┌────────────────────────────────┐                 └───────────────┬───────────────┘
 │   Admin Dashboard (UI)         │                                 │
 │ • Overview KPIs                │ ────────────────────────────────┘
 │ • Customer Segmentation Donut  │
 │ • Top Redemptions Bar Chart    │
 │ • Audit Ledger & Monitoring    │
 └────────────────────────────────┘
                                                    │
                                                    ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
 │                              Agentic Orchestration (LangGraph)                               │
 │                                                                                              │
 │ ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌─────┐│
 │ │   Router   │──>│    Data    │──>│ Analytics  │──>│Eligibility │──>│   Reward   │──>│Resp ││
 │ │   Agent    │   │   Agent    │   │ Agent (ML) │   │   Agent    │   │ Agent (ML) │   │Agent││
 │ └────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘   └─────┘│
 │   Role Guard       MCP Queries     RFM/K-Means      Hard Barriers     Ranking / Laya    JSON │
 │                                                                                              │
 │ ─────────────────────────────── Shared State & Memory ────────────────────────────────────── │
 └──────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                                │
                                                ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                 MCP (Model Context Protocol) Tools                           │
 │ • PostgreSQL MCP        • Inventory MCP        • Campaign MCP        • RAG MCP (Optional)    │
 └──────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                                │
                                                ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   PostgreSQL Database (Neon)                                 │
 │ • customers          • transactions         • inventory                                      │
 │ • campaigns          • rewards_catalogue    • reward_ledger                                  │
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Layers

### 2.1 User Interface Layer (Streamlit)
- **Customer Portal:** Clean member-facing views including account standings, horizontal recommendation cards with instant redemption actions, and real-time ledger histories.
- **Admin Operations:** Executive overview with interactive Donut and Bar charts, customer directory, reward catalogue toggles, inventory replenishments, approval queue management, and model monitoring.

### 2.2 Backend Gateway & API Layer (FastAPI)
- **Schema Validation:** Strict Pydantic models for incoming payloads and API responses.
- **Fail-Closed Authentication:** HTTP Bearer token validation on sensitive approval, redemption, and administrative endpoints.
- **Transactional Row Locking:** Database queries for points debit and budget deductions use `SELECT FOR UPDATE` to prevent race conditions during concurrent user operations.

### 2.3 Agentic Orchestration Layer (LangGraph)
The agentic workflow executes a 6-node state machine:
1. **Router Agent:** Classifies user intent and rejects privilege escalation attempts.
2. **Data Agent:** Invokes approved MCP read tools to retrieve customer loyalty profiles, transaction histories, and inventory levels.
3. **Analytics Agent:** Ingests transaction records and computes Recency, Frequency, Monetary values, and K-Means cluster mappings.
4. **Eligibility Agent:** Evaluates deterministic business rules (points, active tiers, expiry, stock barriers, campaign spend limits) and prunes invalid rewards.
5. **Reward Agent:** Applies multi-objective ranking on feasible candidates using weighted scores and queries the Laya decision adapter with a 0.60 confidence gate.
6. **Response Agent:** Serializes outputs into structured JSON responses with explicit reason codes.

### 2.4 Model Context Protocol (MCP) Tools Layer
Exposes granular database and operational capabilities through standardized MCP interfaces:
- `PostgreSQL MCP`: Read customer context, read transactions, update reward ledger.
- `Inventory MCP`: Check on-hand/reserved stock, reserve units, update physical inventory.
- `Campaign MCP`: Retrieve budget limits, verify committed expenditures.

### 2.5 Data Persistence Layer (PostgreSQL)
- Hosted on Neon Serverless PostgreSQL.
- Implements foreign key integrity, unique indexes on `idempotency_key`, and atomic transaction commits.
