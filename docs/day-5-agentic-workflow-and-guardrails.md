# Day 5 — Agentic Workflow and Guardrails

**Project:** Loyalty and Reward Optimisation with Inventory-Aware Rewards  
**Sprint phase:** Day 5 of the 7-Day Agentic AI Project Sprint  
**Status:** Completed and locally verified by the project owner

## 1. Day 5 Objective

The objective of Day 5 was to orchestrate the reward recommendation workflow and demonstrate controlled, explainable decision-making. The implementation focused on the six-agent LangGraph workflow, approved MCP data access, the Laya decision adapter, execution tracing, API exposure, security guardrails, and safe failure behaviour.

The implementation follows the project's core separation of responsibilities:

- Deterministic business rules decide which rewards are feasible.
- Laya evaluates only the feasible reward candidates.
- LangGraph coordinates the agents and workflow stages.
- MCP exposes approved data-retrieval tools.
- Approval and redemption remain separate application workflows; the recommendation agents do not execute them.

## 2. Six-Agent LangGraph Workflow

The following six agents were connected in the LangGraph state graph:

1. **Router Agent** — classifies the incoming request and selects the workflow route.
2. **Data Agent** — retrieves customer, transaction, reward, campaign, reward-product mapping, and inventory information through approved MCP tools.
3. **Analytics Agent** — runs customer analytics and prepares the analytical context used by later stages.
4. **Eligibility Agent** — applies deterministic eligibility and feasibility checks to reward candidates.
5. **Reward Agent** — passes feasible candidates to the Laya decision adapter and obtains a selected/ranked candidate or a safe fallback result.
6. **Response Agent** — prepares a customer-facing explanation from the workflow result.

The graph uses shared state, registered nodes, conditional edges, and a terminal response stage. Failure or non-success statuses are routed according to the graph's conditional routing logic.

## 3. MCP Integration and Tool Permissions

The MCP server/client integration was used by the Data Agent to access approved read operations:

- `get_customer_profile`
- `get_transaction_history`
- `get_product_inventory`
- `get_campaign_details`
- `get_reward_details`
- `get_reward_product_mappings`
- `get_active_rewards`

The Data Agent uses an explicit allowlist mapping request types to MCP tool names and required parameters. It validates that parameters are dictionaries, checks required values, and rejects unexpected arguments. Approval and redemption operations are not included in this allowlist.

This keeps data retrieval separate from consequential actions. The agentic recommendation workflow is not granted an approval or redemption tool.

## 4. Laya Decision Adapter and Safe Fallback

The Laya adapter receives only feasible candidates. It filters out candidates that are not marked eligible or that contain reason codes, prepares the candidate options, and asks Laya to select a reward.

The adapter validates that the returned reward ID belongs to the submitted candidate set. It also checks the configured minimum confidence threshold (`0.60`). If Laya raises an error, returns an unknown candidate, or returns a confidence value below the configured threshold, the adapter falls back to the deterministic baseline ranker.

The confidence threshold is an implementation setting; it has not been established as a statistically calibrated confidence threshold through a labelled evaluation dataset.

If no feasible candidates exist, the adapter returns an empty result rather than forcing a recommendation.

## 5. Workflow Execution Trace

A workflow runner was added to consume LangGraph updates using `astream(..., stream_mode="updates")`. It accumulates node updates into the final state and records a trace containing:

- Step number
- Node name
- Node status
- Error summary, when present

Unexpected exceptions are converted into a `WORKFLOW_ERROR` result. The runner records the exception type rather than exposing raw exception text, which could contain connection details or other sensitive configuration.

The trace makes the execution path visible for debugging and demonstration.

## 6. Agentic Recommendation API

A separate endpoint was added:

`POST /rewards/agentic-recommendations`

It accepts the existing recommendation request schema, builds the six-agent graph, runs the workflow, and returns:

- Customer ID
- Overall workflow status
- Recommendation result
- Customer-facing final response
- Sanitised node-level execution trace

The existing deterministic endpoint, `POST /rewards/recommendations`, was kept separate and unchanged by this addition. The agentic endpoint does not return internal customer, transaction, inventory, or campaign records. Trace errors are replaced with a generic message rather than returning raw internal error details.

## 7. Guardrails and Security Controls

The Day 5 guardrail work included:

- An explicit MCP tool allowlist for the Data Agent.
- Rejection of unsupported request types.
- Rejection of missing or unexpected tool arguments.
- No approval or redemption capability in the Data Agent's allowed tools.
- Response prompt instructions treating retrieved/user-provided content as untrusted input, not following instructions embedded in it, not revealing system prompts, and not modifying points.
- Sanitised workflow/API trace errors.
- Separation between recommendation generation and approval/redemption execution.

These controls demonstrate restrictions within the agentic workflow. They do not, by themselves, establish complete application-wide authentication and authorisation for every API endpoint; those checks must be independently verified.

## 8. Problems Encountered and How They Were Addressed

### 8.1 Workflow execution was not observable node by node

**Problem:** A successful final graph result alone did not provide a clear record of which agent nodes ran and what status each node returned.

**Resolution:** Added `backend/app/agents/graph_runner.py` to stream LangGraph node updates, accumulate the final state, and create a step-by-step execution trace. Added tests for successful traces, node-reported failures, and unexpected workflow exceptions.

### 8.2 The agentic graph did not have a dedicated API entry point

**Problem:** The existing recommendation endpoint exposed the deterministic recommendation service, not the new six-agent LangGraph workflow. Replacing its behaviour risked affecting existing API consumers.

**Resolution:** Added a separate `POST /rewards/agentic-recommendations` endpoint. The existing `POST /rewards/recommendations` endpoint was retained separately. Added API tests for the response, request context, trace sanitisation, and exclusion of internal customer data.

### 8.3 Agent tool access needed explicit restrictions

**Problem:** The Data Agent needed to retrieve business data without being able to perform consequential approval or redemption actions, and it needed to reject unexpected tool arguments.

**Resolution:** Added/verified an explicit allowlist in `backend/app/agents/data_agent.py`, required-parameter checks, and exact argument-set validation. Security tests verify that approval/redemption request types are rejected without calling the MCP client and that unexpected arguments are rejected.

### 8.4 Internal exception details could leak through workflow traces

**Problem:** Raw exception messages can contain database connection details or other sensitive configuration.

**Resolution:** The workflow runner converts unexpected exceptions into a safe error containing the exception type, and the API replaces node error details with a generic message. Tests verify that a simulated secret connection string is not exposed by the runner or API response.

### 8.5 Analytics test execution depended on dataset path configuration

**Problem:** An analytics test used a dataset path that was affected by shared/global path configuration during test execution.

**Resolution:** The analytics test path handling was corrected so the test uses the intended dataset location consistently. The project owner subsequently confirmed the agent/decision test suite passed.

### 8.6 The live workflow returned no feasible reward for the demonstration customer

**Observed behaviour:** The live API request for customer `12348` completed with overall workflow status `SUCCESS`. The trace showed all six nodes executing successfully, while the Reward Agent returned `NO_FEASIBLE_REWARD` and an empty recommendation list.

**Resolution:** No eligibility or inventory rule was weakened to force a recommendation. The result was treated as a valid business outcome: when no candidate passes the mandatory constraints, the system must not invent or force a reward. The Response Agent generated an explanation for the customer.

This was a valid no-candidate outcome, not a workflow failure.

## 9. Validation Evidence

The project owner reported that the following test groups passed after the corresponding changes:

- Agent, graph, and decision test suite: **71 tests passed** at that validation point.
- Security guardrail tests.
- Graph runner tests.
- Agentic recommendation API tests.
- Combined failure-handling and security/API test runs.

A live request to `POST /rewards/agentic-recommendations` was also executed successfully for customer `12348`. The returned trace showed:

| Step | Node | Result |
|---:|---|---|
| 1 | Router | SUCCESS |
| 2 | Data | SUCCESS |
| 3 | Analytics | SUCCESS |
| 4 | Eligibility | SUCCESS |
| 5 | Reward | NO_FEASIBLE_REWARD |
| 6 | Response | SUCCESS |

The live result contained no recommendations because no feasible reward was available. This is consistent with the project's requirement to return a no-eligible-reward outcome instead of forcing a recommendation.

**Evidence limitation:** The test counts above are the results reported by the project owner during Day 5 validation. They should not be interpreted as a claim that every test in the entire repository passed. A fresh full-suite run is part of Day 6.

## 10. Day 5 Deliverables

- Six-agent LangGraph workflow and conditional routing.
- MCP-backed Data Agent with an explicit read-tool allowlist.
- Laya decision adapter with candidate validation and deterministic fallback.
- Workflow runner with node-level execution tracing.
- Separate agentic recommendation API endpoint.
- Security guardrail tests for prohibited tools and invalid arguments.
- Workflow runner tests for success and failure cases.
- Agentic API tests for request context and sanitised output.
- Live API demonstration with a trace covering all six agents.
- This Day 5 implementation and troubleshooting record.

## 11. Known Limitations and Follow-up Work

- The configured Laya confidence threshold has not been validated/calibrated against a representative labelled dataset.
- A live no-feasible-reward result demonstrates safe filtering, but does not measure recommendation quality or business impact.
- Prompt-level instructions are not a substitute for deterministic security controls and API authorisation.
- Application-wide authentication and authorisation for approval/redemption endpoints require independent verification.
- A fresh full test-suite run, systematic edge-case testing, Laya-versus-baseline evaluation, and at least two fully documented defect investigations belong to Day 6.
- The customer-facing phrase suggesting that the system will keep monitoring the reward catalogue should not imply that a background monitoring service exists unless such a service is implemented.

## 12. Day 5 Completion Summary

Day 5 implementation and its reported validation were completed. The six-agent workflow was connected to MCP data retrieval and the Laya decision adapter, exposed through a separate API endpoint, and equipped with node-level traces, tool restrictions, safe error handling, and guardrail tests.

The live demonstration completed all six workflow stages and correctly returned `NO_FEASIBLE_REWARD` when no candidate met the business constraints. Day 6 will focus on broader testing, security verification, evaluation, defect investigations, and known-issues documentation.
