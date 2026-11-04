Project 1: Loyalty and Reward Optimisation with Inventory-Aware Rewards
Duration: 7 Days Domain: Customer Loyalty, Rewards, Inventory and
Fulfilment Difficulty: Intermediate to Advanced Project Type: Data
Science + Backend Engineering + Agentic Decision Systems

Primary Technologies: Python, Pandas, NumPy, FastAPI, Pydantic,
PostgreSQL, Pytest

Decision Layer: OpenJEV or Laya, selected after technical evaluation

Other Technologies: LangGraph, Scikit-learn, MCP, Langfuse, Docker

Frontend: React.js/Streamlit, HTML, CSS and JavaScript

1.  Business Problem Businesses use loyalty points, vouchers, discounts
    and cashback to encourage repeat purchases. However, reward
    programmes can become inefficient when offers are poorly targeted,
    campaign budgets are exceeded, or recommended products have
    insufficient inventory.

Common business problems include:

High-value customers receive irrelevant rewards. Inactive customers
receive the same promotions as frequent customers. A reward is
recommended despite insufficient stock. Campaign spending exceeds the
available budget. Customers redeem rewards without having enough points.
Duplicate requests create duplicate reward transactions. Business teams
cannot understand why an offer was recommended. An automated decision
system recommends an attractive but operationally infeasible option. The
business needs an application that combines customer purchasing
behaviour, reward policies, campaign constraints and inventory
availability to recommend suitable offers.

1.1 Project Objective Develop an inventory-aware reward recommendation
system that:

Analyses historical retail transactions. Segments customers using
Recency, Frequency and Monetary (RFM) analysis. Maintains synthetic
loyalty profiles, points balances and reward records. Validates reward
eligibility using deterministic business rules. Checks stock
availability and replenishment constraints. Uses a decision layer
powered by OpenJEV or Laya to compare valid alternatives. Uses an
optional agent workflow to coordinate tools and prepare recommendation
proposals. Exposes the workflow through FastAPI. Prevents duplicate
redemptions through idempotency and transactional persistence. Records
structured logs, automated tests and troubleshooting evidence. 1.2
Proposed Solution The system will combine customer analytics,
deterministic policy enforcement and a decision-support layer.

The deterministic policy engine establishes which rewards are permitted.
OpenJEV or Laya can then evaluate the permitted alternatives using a
structured choice or scoring task. An optional LangGraph workflow can
coordinate customer analysis, policy checks, decision evaluation and
approval preparation.

The application must preserve four separate responsibilities:

Business rules: Determine eligibility and enforce non-negotiable
constraints. Decision layer: Compare valid alternatives against defined
business objectives. Agent orchestration: Coordinate tools and prepare
structured proposals. Execution layer: Revalidate conditions, obtain
required approval and commit the redemption transaction. The decision
model must never be the authority for points balances, reward expiry,
inventory quantities, campaign budgets or successful redemption.

2.  Business Scenario A retailer launches a loyalty campaign with a
    budget of ₹50,000 and a catalogue of rewards linked to products with
    different stock levels.

A customer with substantial historical spending requests a
recommendation.

The application must:

Retrieve the customer's RFM segment. Retrieve the synthetic loyalty tier
and points balance. Retrieve the active reward catalogue. Validate
points, eligibility and expiry. Check linked inventory and replenishment
restrictions. Calculate campaign commitments using a documented
accounting policy. Exclude every reward that violates a mandatory
constraint. Evaluate the remaining alternatives through the decision
layer. Return ranked options and a structured explanation. Route the
proposal for approval. Revalidate current conditions before redemption.
Record the result in the reward ledger. If no feasible reward remains,
the application must return NO_ELIGIBLE_REWARD rather than force a
recommendation.

3.  Dataset Requirements 3.1 Primary Dataset: UCI Online Retail II
    Source: https://archive.ics.uci.edu/dataset/502/online_retail%2Bii

Use this dataset as the primary source for historical purchasing
behaviour. It contains retail transaction information, including invoice
identifiers, product codes, descriptions, quantities, invoice dates,
prices, customer identifiers and countries.

Data preparation requirements Preserve downloaded files in data/raw/.
Inspect schema, row counts, duplicates and missing values. Convert
transaction dates into a consistent datetime format. Identify cancelled
invoices using documented source conventions. Identify returns and
negative quantities. Validate quantities and unit prices. Exclude or
separately account for cancellations and returns. Create customer-level
analytical features. Record all cleaning decisions in the data
dictionary. RFM features Recency: Days since the customer's most recent
qualifying purchase. Frequency: Number of qualifying purchases, using a
consistent invoice-counting convention. Monetary: Customer purchase
value using a documented gross or net accounting convention. Use a fixed
historical analysis date, such as one day after the maximum qualifying
transaction date. Do not silently use the current date for historical
calculations.

3.2 Secondary Dataset: M5 Forecasting Source:
https://www.kaggle.com/competitions/m5-forecasting-accuracy

Potential uses:

Explore product-level demand patterns. Build an optional demand
forecasting baseline. Investigate how expected demand might influence
inventory risk. This dataset is optional for the seven-day MVP. Its
identifiers must not be assumed to correspond to Online Retail II
products.

3.3 Secondary Dataset: DataCo Smart Supply Chain Source:
https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis

Potential uses:

Explore order and shipping operations. Analyse fulfilment delays. Extend
the project with supply chain risk indicators. This dataset is also
optional. Do not merge its customer or product identifiers with Online
Retail II as though the records belong to the same business.

3.4 Synthetic Loyalty and Inventory Data Online Retail II does not
provide a complete loyalty ledger, points balance, campaign budget or
authoritative inventory system. Create clearly labelled synthetic
records for the MVP.

Customer loyalty profile customer_id loyalty_tier points_balance
profile_status profile_created_at Reward catalogue reward_id reward_name
reward_type reward_value points_required eligible_tiers valid_from
valid_until minimum_purchase_value status Inventory snapshot product_id
on_hand_stock reserved_stock available_stock, if supplied by the source
reorder_level replenishment_date inventory_updated_at Reward-product
mapping reward_id product_id minimum_stock_required
inventory_constraint_type Campaign budget campaign_id budget_limit
committed_amount approved_amount campaign_status Reward ledger
redemption_id idempotency_key request_hash customer_id reward_id
campaign_id points_debited reward_cost redemption_status created_at Use
synthetic identifiers for demonstration. Document how synthetic records
are generated and how they relate to the source transaction data.

Dataset rule: The source datasets do not automatically share customer,
product or inventory identifiers. Any synthetic mapping must be
explicitly documented and must not be represented as a real business
relationship.

4.  User Stories and Acceptance Criteria US-01: Customer Segmentation As
    a loyalty manager, I want to segment customers using purchasing
    behaviour so that I can identify valuable, regular and inactive
    customer groups.

Acceptance criteria:

Generate customer-level RFM features. Show segment counts and relevant
summary metrics. Handle missing customer IDs appropriately. Handle
cancelled invoices and returns according to documented rules. Document
the reference date and feature calculations. Validate the resulting
customer table for unexpected duplicates and missing values.
Deliverables: RFM table, segment distribution, summary metrics and data
quality report.

US-02: Inventory-Aware Reward Recommendation As a campaign manager, I
want to recommend eligible rewards within budget so that campaigns
remain commercially viable.

Acceptance criteria:

Validate customer tier, points balance, reward status and expiry. Check
inventory constraints before ranking. Enforce campaign budget limits
deterministically. Exclude invalid rewards before calling the decision
model. Compare only feasible alternatives. Explain recommendations using
structured reason codes and decision evidence. Return a clear
no-eligible-reward outcome when appropriate. Revalidate constraints
before redemption. Deliverables: Ranked options, reward costs,
eligibility results, inventory status and decision rationale.

US-03: Reward Integrity As a system administrator, I want duplicate
redemption requests to be handled safely so that a reward cannot be
redeemed twice through repeated requests.

Acceptance criteria:

Require an idempotency key. Enforce uniqueness through database
constraints. Return the original outcome for an identical repeated
request. Reject reuse of the same key for a conflicting payload. Test
concurrent requests. Apply points deductions and budget commitments
atomically. Record redemption outcomes. Deliverables: Persistent ledger
and duplicate-request test results.

US-04: Monitoring and Troubleshooting As a developer, I want structured
logs and automated tests so that I can diagnose invalid recommendations
and transaction errors.

Acceptance criteria:

Log request IDs, latency, outcomes and error codes. Avoid logging
unnecessary sensitive customer information. Test budget limits, expiry,
inventory constraints and invalid inputs. Record tool and decision-layer
failures. Investigate and document at least two actual defects. Add
regression tests for the investigated defects. Deliverables: Test
report, structured logs and root-cause analysis.

US-05: Controlled Approval As a campaign manager, I want to approve
reward proposals before redemption so that automated recommendations do
not bypass business controls.

Acceptance criteria:

Generate a proposal without executing a redemption. Display eligibility,
cost, inventory and campaign context. Require the configured approval
action. Revalidate current constraints at redemption time. Record the
approval outcome. Reject the redemption if any mandatory constraint has
changed. Deliverables: Approval workflow and auditable redemption
outcome.

5.  Seven-Day Sprint Plan Day 1 --- Requirements and Data Schema Goal:
    Define the business problem, decision criteria and application
    contracts.

Tasks:

Define business KPIs and reward rules. Establish hard constraints and
optimisation objectives. Review dataset availability and licensing.
Design synthetic loyalty, reward, inventory and campaign records. Define
API contracts. Review OpenJEV and Laya documentation. Select an initial
decision-layer integration approach. Set up the repository.
Deliverables:

docs/problem_statement.md docs/user_stories.md
docs/dataset_documentation.md Initial architecture diagram.
Decision-layer selection note. Acceptance criteria. Day 2 --- Data
Preparation and Baseline Analysis Goal: Build reproducible customer
analytics.

Tasks:

Load Online Retail II. Profile missing values and duplicates. Handle
cancellations and returns. Calculate RFM features. Create a baseline
segmentation strategy. Generate synthetic loyalty and inventory records.
Validate identifiers and relationships. Save processed outputs
separately from raw data. Deliverables:

notebooks/01_data_understanding.ipynb notebooks/02_eda.ipynb RFM table
and segment summaries. Data quality report. Synthetic sample data. Day 3
--- Deterministic Policy Engine Goal: Implement business truth before
optimisation.

Tasks:

Implement eligibility checks. Implement points and expiry validation.
Implement inventory and replenishment rules. Implement campaign budget
calculations. Define structured rejection reason codes. Build the
feasible reward candidate set. Implement a deterministic baseline
ranker. Write unit tests. Deliverables:

Tested policy engine. Feasible candidate set. Baseline ranking
implementation. Unit test report. Definition of done: Invalid rewards
cannot enter the final candidate set.

Day 4 --- FastAPI and Persistence Goal: Expose the policy engine through
a reliable API.

Tasks:

Create the FastAPI application. Add Pydantic request and response
schemas. Implement customer, recommendation, approval and redemption
endpoints. Configure PostgreSQL or SQLite for a simplified local
prototype. Create database models and repositories. Implement
idempotency. Add transactional ledger operations. Write API and
integration tests. Deliverables:

Working API. Database schema. API contract tests. Persistent reward
ledger. OpenAPI documentation. Day 5 --- OpenJEV or Laya Decision Layer
Goal: Integrate the selected decision engine and compare it against the
baseline.

Tasks:

Verify the exact package, API or model interface. Implement a decision
adapter. Define typed decision inputs and outputs. Pass only
policy-approved reward candidates to the decision layer. Define the
decision question and business objective. Evaluate selected options
against the deterministic baseline. Add confidence or uncertainty
handling where supported. Reject malformed, unknown or invalid candidate
selections. Add timeout and failure handling. Integrate the decision
step into the optional LangGraph workflow. Deliverables:

Decision adapter. Working recommendation workflow. Decision-layer tests.
Baseline-versus-decision-layer evaluation. Documented framework
limitations. Fallback: If integration is unreliable, retain the
deterministic baseline ranker. The MVP must still enforce all mandatory
business constraints.

Day 6 --- Testing, Security and Troubleshooting Goal: Verify correctness
and investigate defects.

Tasks:

Run unit, integration and API tests. Test expired rewards and
insufficient points. Test stock shortages and replenishment
restrictions. Test exhausted campaign budgets. Test duplicate and
concurrent redemption requests. Test decision-engine timeouts and
malformed outputs. Test safe fallback behaviour. Verify database
rollback and transaction consistency. Review logging and secret
management. Investigate at least two real defects. Deliverables:

Regression test suite. Security test results. Root-cause notes. Test
execution report. Corrected defects. Day 7 --- Demonstration and
Handover Goal: Demonstrate the complete business workflow.

Tasks:

Run the application from a clean environment. Load the sample dataset.
Demonstrate RFM segmentation. Show deterministic eligibility checks.
Compare the baseline and selected decision layer. Demonstrate stock and
budget rejection. Demonstrate approval and redemption. Demonstrate
idempotency. Review test results and limitations. Complete the README
and architecture diagram. Deliverables:

Working MVP. Complete repository. Demonstration script. Architecture and
workflow documentation. Test and troubleshooting reports. Final
evaluation summary. 6. Architecture and Decision-Layer Integration 6.1
High-Level Architecture \`\`\`Online Retail II + Synthetic
Loyalty/Inventory Data

                         |

                         v

               Data Preparation Layer

                         |

                         v

                  RFM Analytics

                         |

                         v

              Customer and Reward Data

                         |

                         v

           Deterministic Policy Engine

          /              |              \

Eligibility Inventory Budget

     Checks           Checks           Checks

          \              |              /

                         v

               Feasible Reward Set

                         |

                         v

              Decision Adapter Layer

                         |

                  OpenJEV or Laya

                         |

                         v

              Selected / Ranked Option

                         |

                         v

             Deterministic Validation

                         |

                         v

             Explanation and Proposal

                         |

                         v

                Approval Workflow

                         |

                         v

              Final Policy Recheck

                         |

                         v

              Atomic Redemption

                         |

                         v

               Reward Ledger + Logs

\`\`\`6.2 Deterministic Policy Layer The policy engine is responsible
for:

Customer eligibility. Points balance. Reward validity and expiry.
Product stock constraints. Replenishment constraints. Campaign budget.
Redemption integrity. Mandatory business restrictions. These rules must
be implemented in ordinary application code and covered by tests. An LLM
must not override them.

6.3 Decision Layer: OpenJEV or Laya OpenJEV and Laya are candidate
technologies for structured decision tasks, but their exact interfaces
and supported models depend on the specific implementation selected.

OpenJEV documentation --- documents structured choice, score and
yes/no-style decision requests. Laya documentation --- documents typed
decision tasks, routing, evaluation and integration options. Before
implementation, verify the selected project's current documentation,
package identity, version, licence, deployment requirements and API
compatibility. Do not assume every project using the OpenJEV name
implements the same interface.

Role of the decision layer The decision layer receives a bounded set of
feasible reward options and evaluates which option best matches the
defined decision criteria.

For example, it may compare:

Customer-segment relevance. Reward attractiveness. Points required.
Estimated campaign cost. Inventory suitability. Campaign objective. Its
output should be a structured choice or score that the application can
validate.

The decision layer does not perform the redemption transaction. It does
not own the authoritative points balance, campaign budget or inventory
record.

Example decision request The application can provide a structured state
containing:

Customer segment. Campaign objective. Approved reward candidate IDs.
Documented attributes for each candidate. Decision criteria and
priorities. The question could be:

"Among the supplied eligible reward options, which best matches the
campaign objective while prioritising customer relevance, lower campaign
cost and inventory suitability?"

The candidate IDs must come from the policy engine, not from free-form
model generation.

Example decision output \`\`\`{

"selected_reward_id": "RWD-101",

"decision_status": "candidate_selected",

"candidate_set_version": "v1",

"validation_status": "pending"

}

\`\`\`This is an illustrative application-level response schema, not a
claimed native OpenJEV or Laya response format.

The service must verify that the selected ID exists in the submitted
candidate set and recheck all mandatory constraints before approval or
execution.

Confidence and uncertainty If the selected implementation returns
probabilities or confidence information, evaluate those signals on
representative labelled examples.

Do not treat model confidence as a guarantee of correctness. If the
result is ambiguous, invalid or below a validated threshold, route the
proposal for review or use the deterministic baseline.

What the decision layer does not replace RFM feature engineering.
Deterministic eligibility rules. Budget accounting. Inventory
validation. Database transactions. Idempotency. Approval controls.
Automated testing. 6.4 Decision Objectives and Constraints Separate hard
constraints from optimisation objectives.

Hard constraints --- must always hold

The customer is eligible. The reward is active and unexpired. Points
requirements are satisfied. Stock requirements are satisfied. Campaign
budget is not exceeded. The redemption is not duplicated. Optimisation
objectives --- can be balanced

Improve reward relevance. Prefer attractive rewards for the target
segment. Reduce reward cost. Prefer better inventory availability.
Support the stated campaign objective. A weighted baseline may use:

score = w1 × relevance + w2 × reward_value + w3 ×
inventory_suitability - w4 × cost_penalty

Document feature scaling and weights. Compare this baseline with the
selected decision engine using the same candidate set and constraints.

The weighted score is a ranking mechanism, not evidence of incremental
retention or profitability.

6.5 Agent Orchestration LangGraph is optional. If used, it should
coordinate the workflow:

Parse the request. Retrieve the customer segment. Retrieve active
rewards. Invoke deterministic policy tools. Build the feasible candidate
set. Call the decision adapter. Validate the returned candidate.
Generate a recommendation proposal. Route for approval. Revalidate
before redemption. MCP is also optional and can expose approved
capabilities as tools when integration with other applications is
required.

An agent must not directly modify points, budgets or inventory merely
because the decision model selected an option.

7.  Reward Business Rules 7.1 Eligibility A reward is eligible only if
    every applicable mandatory condition passes:

Customer profile is active. Reward is active. Current evaluation time is
within the reward's validity period. Customer tier meets any applicable
restriction. Available points are sufficient. Minimum purchase
requirements are met. Inventory satisfies the configured constraints.
Campaign is active. Sufficient campaign budget remains. No applicable
business restriction prevents redemption. Use structured reason codes
such as:

CUSTOMER_INACTIVE REWARD_EXPIRED INSUFFICIENT_POINTS TIER_NOT_ELIGIBLE
INSUFFICIENT_STOCK REPLENISHMENT_CONSTRAINT CAMPAIGN_INACTIVE
BUDGET_EXCEEDED 7.2 Inventory Use a documented inventory convention. For
example:

available_to_promise = on_hand_stock - reserved_stock

Do not subtract reserved stock again if the source's available-stock
field already excludes it.

Implement at least one minimum-stock rule and one replenishment rule.
Optionally reject stale inventory snapshots using a configured freshness
threshold.

7.3 Campaign Budget Define:

available_budget = budget_limit - active_commitments

Document what constitutes an active commitment and apply the same
convention during recommendation, approval and redemption.

Prevent concurrent requests from consuming the same remaining budget
using atomic database operations or appropriate transaction locking.

7.4 Reward Cost Distinguish:

Reward face value. Estimated campaign cost. Points debited. Actual
settlement cost, if applicable. Do not assume these quantities are
interchangeable. Select one documented cost convention for the MVP.

7.5 Redemption The redemption workflow must separate recommendation,
approval, final validation and transaction commitment.

The final transaction should atomically update the relevant points
balance, campaign commitment and reward ledger. If stock reservation is
implemented, it must be coordinated through an appropriate transactional
or reservation mechanism.

8.  Common Project Folder Structure Use the following common structure
    as the repository template for this project and related agentic
    decision-system projects.

\`\`\`project-name/

│

├── data/

│ ├── raw/ \# Original datasets; never overwrite

│ ├── interim/ \# Partially cleaned datasets

│ ├── processed/ \# Model-ready data

│ └── sample/ \# Small safe demo datasets

│

├── notebooks/

│ ├── 01_data_understanding.ipynb

│ ├── 02_eda.ipynb

│ └── 03_baseline_experiments.ipynb

│

├── backend/

│ ├── app/

│ │ ├── main.py \# FastAPI application

│ │ ├── config.py \# Environment configuration

│ │ │

│ │ ├── api/

│ │ │ ├── routes/

│ │ │ └── schemas/ \# Pydantic request/response schemas

│ │ │

│ │ ├── agents/

│ │ │ ├── graph.py \# Optional LangGraph workflow

│ │ │ ├── state.py \# Shared graph state

│ │ │ ├── supervisor.py

│ │ │ ├── prompts.py

│ │ │ └── nodes/ \# Specialist agent nodes

│ │ │

│ │ ├── decision/

│ │ │ ├── models.py \# Decision request/response contracts

│ │ │ ├── objectives.py \# Documented optimisation objectives

│ │ │ ├── constraints.py \# Decision input constraints

│ │ │ ├── baseline_ranker.py \# Deterministic baseline

│ │ │ ├── optimizer_adapter.py \# Common decision interface

│ │ │ ├── openjev_adapter.py \# If OpenJEV is selected

│ │ │ ├── laya_adapter.py \# If Laya is selected

│ │ │ └── evaluator.py \# Baseline comparison

│ │ │

│ │ ├── services/ \# Application workflows

│ │ ├── domain/ \# Deterministic business rules

│ │ │ ├── eligibility.py

│ │ │ ├── inventory.py

│ │ │ └── budget.py

│ │ │

│ │ ├── ml/

│ │ │ ├── features.py

│ │ │ ├── train.py

│ │ │ ├── predict.py

│ │ │ └── evaluate.py

│ │ │

│ │ ├── rag/

│ │ │ ├── ingestion.py

│ │ │ ├── embeddings.py

│ │ │ ├── retriever.py

│ │ │ └── vector_store.py

│ │ │

│ │ ├── mcp_server/

│ │ │ ├── server.py

│ │ │ └── tools/

│ │ │

│ │ ├── db/

│ │ │ ├── session.py

│ │ │ ├── models.py

│ │ │ └── repositories/

│ │ │

│ │ ├── guardrails/

│ │ ├── middleware/

│ │ ├── security/

│ │ └── observability/

│ │

│ └── requirements.txt

│

├── frontend/

│ ├── index.html

│ ├── styles/

│ └── scripts/

│

├── tests/

│ ├── unit/

│ ├── integration/

│ ├── api/

│ ├── agents/

│ ├── decision/

│ └── security/

│

├── scripts/

│ ├── prepare_data.py

│ └── bootstrap.py

│

├── docs/

│ ├── problem_statement.md

│ ├── user_stories.md

│ ├── architecture.md

│ ├── dataset_documentation.md

│ ├── decisions.md

│ ├── decision_layer_evaluation.md

│ └── troubleshooting.md

│

├── .env.example

├── .gitignore

├── Dockerfile

├── docker-compose.yml

├── Makefile

├── pytest.ini

└── README.md

\`\`\`Folder implementation rules domain/ owns authoritative business
rules. decision/ compares feasible alternatives and evaluates decision
quality. agents/ coordinates tools and workflow state. services/
coordinates domain logic, decision execution and persistence.
api/schemas/ validates API contracts. db/ manages persistence and
repositories. guardrails/ validates model and agent behaviour where
applicable. middleware/ handles request IDs and HTTP-level concerns.
security/ handles authentication and authorisation. observability/
captures logs, latency and failures. tests/decision/ evaluates the
selected engine and deterministic baseline. docs/ records architecture,
assumptions and measured results. Keep the structure reusable but
implement only the modules required for the seven-day MVP. RAG, MCP and
ML training are optional extensions, not mandatory prerequisites.

9.  API Design Suggested endpoints:

Method

Endpoint

Purpose

GET

/health

Application health

GET

/customers/{customer_id}/profile

Retrieve customer profile

GET

/customers/{customer_id}/segments

Retrieve customer segment

POST

/rewards/recommendations

Generate eligible recommendations

POST

/rewards/approvals

Record approval decision

POST

/rewards/redemptions

Execute validated redemption

GET

/rewards/redemptions/{redemption_id}

Retrieve redemption status

GET

/campaigns/{campaign_id}/budget

Retrieve campaign budget state

Use Pydantic to validate request and response schemas. Keep API routes
thin and delegate policy and decision logic to the appropriate modules.

Recommendation request example \`\`\`{

"customer_id": "CUST-1001",

"campaign_id": "CAMP-001",

"limit": 5

}

`Recommendation response example`{

"customer_id": "CUST-1001",

"campaign_id": "CAMP-001",

"status": "recommendations_available",

"recommendations": \[

    {

      "reward_id": "RWD-101",

      "eligible": true,

      "points_required": 1000,

      "estimated_campaign_cost": 150,

      "inventory_status": "available",

      "decision_status": "selected",

      "reason_codes": [

        "CUSTOMER_ELIGIBLE",

        "POINTS_SUFFICIENT",

        "STOCK_AVAILABLE",

        "BUDGET_AVAILABLE"

      ]

    }

\]

}

\`\`\`The identifiers, values and results above are illustrative. They
are not measured results from the source dataset or native outputs from
OpenJEV or Laya.

API error behaviour HTTP 422 for malformed requests. HTTP 404 for
unknown customers or resources. HTTP 409 for conflicting idempotency
keys. Structured business rejection for insufficient points, stock or
budget. Safe HTTP 500 responses for unexpected failures. Do not expose
stack traces, database credentials or other sensitive internal details
to API clients.

10. Essential Engineering Rules Rule 1: Domain Owns Business Truth
    Reward calculations, eligibility, expiry, stock and campaign
    constraints must remain deterministic.

Rule 2: Decision Layer Chooses Among Feasible Options OpenJEV or Laya
must receive only validated candidates. It may select or score
alternatives but must not relax mandatory constraints.

Rule 3: Agents Own Orchestration Agents coordinate approved tools and
generate proposals. They cannot independently authorise reward
transactions.

Rule 4: Services Own Application Workflows Services coordinate
validation, decision evaluation, approval, persistence and redemption.

Rule 5: Schemas Enforce Contracts All external inputs and decision
outputs must be validated. Reject unknown reward IDs, malformed
responses and invalid state transitions.

Rule 6: Transactions Must Be Atomic Prevent duplicate redemptions and
budget overspending through database constraints, appropriate locking
and atomic updates.

Rule 7: Observability Enables Diagnosis Record request IDs, outcomes,
latency and relevant errors. Mask sensitive data and never log
credentials.

Rule 8: Data Must Be Traceable Keep raw datasets immutable and document
synthetic data, assumptions and transformations.

Rule 9: Decision Failures Must Be Safe If OpenJEV or Laya times out or
returns an invalid result, apply the documented fallback policy. The
fallback must use the same deterministic eligibility and budget checks.

Rule 10: Evaluation Must Be Evidence-Based Compare the decision layer
against the deterministic baseline using reproducible tests. Do not
claim a superior model without measured evidence.

11. Testing Strategy 11.1 Unit Tests Test:

Valid and invalid customer eligibility. Sufficient and insufficient
points. Active and expired rewards. Eligible and ineligible tiers.
Sufficient and insufficient stock. Replenishment constraints. Exact
budget boundary conditions. Ranking of eligible rewards. No eligible
candidate. Invalid decision output. 11.2 Integration Tests Test:

Successful ledger insertion. Correct points deduction. Consistent
campaign commitment. Transaction rollback. Duplicate idempotency key.
Conflicting payload for the same key. Concurrent redemption attempts.
Inventory revalidation. Decision-layer failure and fallback. 11.3
Decision-Layer Tests Test OpenJEV or Laya against a deterministic
baseline using identical candidate sets.

Include:

Candidate selection accuracy against labelled examples. Feasibility of
selected options. Handling of uncertain or ambiguous decisions.
Behaviour when candidate descriptions change. Invalid or unknown
candidate IDs. Timeouts and service errors. Repeatability where
deterministic behaviour is expected. Latency and resource usage. Where
the selected framework returns probabilities or confidence scores,
evaluate their reliability on held-out labelled examples rather than
assuming they are calibrated.

11.4 Security Tests Include:

Input validation. Authentication and authorisation checks. Secret
management. Unsafe logging checks. Rate limiting where appropriate. Tool
permission checks. Prompt injection and tool-abuse scenarios if an LLM
is used. Prevention of unauthorised redemptions. 11.5 Troubleshooting
Requirement Investigate at least two actual defects. For each, document:

Defect ID. Expected and actual behaviour. Reproduction steps. Relevant
logs or request ID. Root cause. Corrective action. Regression test.
Verification result. Possible areas include duplicate redemption,
incorrect budget accounting, timezone errors, invalid inventory
calculations or malformed decision outputs. These are examples, not
defects to claim as discovered without evidence.

12. Success Metrics Business and Data Metrics Customer segmentation
    coverage. Segment interpretability and RFM summary quality.
    Percentage of returned recommendations that satisfy all eligibility
    rules. Budget violations. Inventory compliance. Duplicate redemption
    prevention. Recommendation relevance against documented criteria.
    Decision-Layer Metrics Selection quality against labelled decisions.
    Feasibility rate of selected candidates. Objective value under the
    documented scoring policy. Decision latency. Failure and fallback
    rates. Sensitivity to changes in candidate descriptions.
    Reproducibility where expected. Engineering Metrics Unit,
    integration and API test results. Critical defects resolved. API
    latency. Database transaction failure rate. Decision-layer timeout
    rate. LLM token usage and cost, if applicable. Setup and deployment
    reproducibility. Targets:

Reward eligibility violations: zero in validated recommendation outputs.
Successful redemption budget violations: zero in automated tests.
Duplicate successful redemptions from repeated identical requests: zero
in the defined test suite. Inventory constraint violations: zero in
applicable tests. Report actual measurements from the implementation. Do
not invent performance results or infer production readiness from the
prototype.

13. Final Deliverables Business and Data Problem statement. User stories
    and acceptance criteria. Dataset source notes and data dictionary.
    Data quality report. RFM table and segment analysis. Synthetic
    loyalty and inventory data. Reward policy specification. Application
    and Decision Layer Working FastAPI backend. Pydantic request and
    response schemas. Deterministic eligibility and budget engine.
    Inventory-aware reward filtering. Decision adapter for OpenJEV or
    Laya, if selected. Deterministic baseline ranker. Decision-layer
    evaluation report. Approval workflow. Persistent reward ledger.
    Idempotent redemption implementation. Basic frontend or API
    demonstration. Quality and Handover Unit, integration and API tests.
    Decision-layer tests. Security checks. Duplicate and concurrency
    test results. Structured logging. At least two documented defect
    investigations. Architecture diagram. README and setup instructions.
    .env.example and .gitignore. Sample recommendation outputs.
    Troubleshooting report. Known limitations and future improvements.
    Final demonstration script.
14. Final Demonstration Scenario The team must demonstrate the complete
    business workflow.

Step 1 --- Customer analytics: Load the processed dataset and display
the RFM segment of a demonstration customer.

Step 2 --- Reward catalogue: Show available synthetic rewards, points
requirements, validity and inventory constraints.

Step 3 --- Policy evaluation: Show how the deterministic engine filters
eligible and ineligible rewards.

Step 4 --- Decision comparison: Compare the deterministic baseline with
OpenJEV or Laya using the same feasible candidate set.

Step 5 --- Inventory restriction: Reduce stock in the test environment
and demonstrate that an affected reward is excluded.

Step 6 --- Budget restriction: Reduce the available campaign budget and
demonstrate that an unaffordable reward cannot be redeemed.

Step 7 --- Approval: Generate a proposal and complete the configured
approval step.

Step 8 --- Redemption: Execute the redemption and show the ledger entry,
points debit and budget commitment.

Step 9 --- Idempotency: Submit the same request with the same
idempotency key and demonstrate that no additional redemption is
created.

Step 10 --- Failure handling: Simulate a decision-layer timeout and
demonstrate the configured safe fallback.

Step 11 --- Evaluation: Present test results, decision-layer comparison,
defects investigated and known limitations.

Use a small synthetic demonstration dataset so the workflow is
repeatable.

15. Expected Business Outcome and Limitations The project should
    demonstrate how historical purchasing data, explicit loyalty
    policies, inventory constraints and a structured decision layer can
    support more controlled reward recommendations.

The MVP is successful if it demonstrates:

Reproducible customer segmentation. Deterministic eligibility
enforcement. Inventory-aware recommendation filtering. Campaign budget
compliance. Decision-layer evaluation against a baseline. Safe approval
and redemption. Idempotent transaction processing. Automated tests and
reproducible documentation. The system does not, by itself, establish an
increase in customer retention, revenue or profitability. Such claims
require a suitable evaluation design and, where appropriate, a
controlled experiment.

Likewise, integrating OpenJEV or Laya does not automatically improve
business decisions. The selected technology must demonstrate measurable
value against the baseline while maintaining mandatory constraints.

Final principle: The deterministic policy engine defines what is
permitted. OpenJEV or Laya evaluates which permitted option is
preferable. The agent coordinates the workflow. The application service
controls approval and execution. The database preserves transaction
integrity.
