**Project Overview**

**Project name:** 7-Day Agentic AI Project Sprint

**Duration:** 7 days

**Platform:** Linear.app

**Objective:** Design, implement, test, and demonstrate a working AI/ML solution that addresses a defined business problem using a structured engineering workflow.

Every candidate must follow the same execution process, maintain progress in Linear, and submit verifiable evidence for completed tasks.

## 1. Project Rules

1. Review the assigned project documentation and `skillguide.md` before implementation.
2. Prepare an **Agentic System Flow Diagram** and complete **Dataset Preparation** before starting the core implementation.
3. Break work into small, trackable Linear issues.
4. Every issue must have an owner, clear acceptance criteria, and a deliverable.
5. Update issue status regularly and add evidence before marking an issue complete.
6. Document assumptions, missing data, synthetic data, design decisions, and blockers.
7. Use Git commits and pull requests to demonstrate implementation progress.
8. Do not claim model accuracy, business impact, or production readiness without supporting evidence.
9. Raise questions and blockers early rather than waiting until the end of the sprint.
10. Complete the final demo and documentation within the seven-day timeline.

## 2. Linear Project Setup

### Recommended workflow statuses

- **Backlog:** Identified but not yet scheduled.
- **Todo:** Ready to begin.
- **In Progress:** Currently being implemented.
- **In Review:** Awaiting review or validation.
- **Done:** Acceptance criteria met and evidence attached.
- **Blocked:** Cannot proceed due to a dependency or unresolved issue.

### Labels

- `Planning`
- `Data`
- `Architecture`
- `ML`
- `Agentic-AI`
- `Backend`
- `Frontend`
- `Testing`
- `Security`
- `Documentation`
- `Review`
- `Blocked`

### Priority levels

- **Urgent:** Blocks the project or threatens a critical requirement.
- **High:** Required for the working end-to-end solution.
- **Medium:** Improves evaluation, usability, or reliability.
- **Low:** Optional enhancement if time permits.

### Issue template

Each issue should contain:

**Objective:** What needs to be accomplished?

**Tasks:** Specific steps required.

**Acceptance criteria:** Conditions that must be met for completion.

**Deliverable:** Diagram, dataset, code, API, test report, or documentation.

**Evidence:** GitHub commit/PR, screenshot, test output, notebook, or document link.

**Dependencies/blockers:** Any prerequisite or unresolved issue.

---

## 3. Seven-Day Sprint Plan

### Day 1 — Requirements, Architecture and Data Preparation

**Goal:** Establish a clear understanding of the problem and prepare the implementation foundation.

**Issues to create:**

1. **Review Project Documentation**
   - Read the assigned project brief and `skillguide.md`.
   - Identify the business problem, users, expected outcomes, constraints, and deliverables.
   - Record unresolved questions.
   **Acceptance criteria:** A concise requirements summary and a list of clarified or outstanding questions are documented.
2. **Create Agentic System Flow Diagram**
   - Map the end-to-end workflow.
   - Identify agents or workflow stages, tools, APIs, data sources, decision points, guardrails, and human approval steps.
   - Show error handling and fallback paths.
   - Distinguish deterministic business rules from model or LLM decisions.
   **Acceptance criteria:** A reviewed flow diagram is attached to the issue and matches the planned implementation.
3. **Prepare and Validate the Dataset**
   - Download the selected dataset and record its source and license.
   - Inspect schema, data types, missing values, duplicates, outliers, and target availability.
   - Define cleaning and transformation rules.
   - Document synthetic fields and assumptions.
   - Save a reproducible preparation script or notebook.
   **Acceptance criteria:** The prepared dataset, data dictionary, source details, and validation summary are available.
4. **Define Technical Architecture and Repository**
   - Finalise the technology stack and folder structure.
   - Create the Git repository, environment configuration, and README.
   - Document components and their responsibilities.
   **Acceptance criteria:** The repository structure is committed, setup instructions work, and the architecture is documented.

**Day 1 deliverables:** Requirements summary, agentic flow diagram, validated dataset, data dictionary, architecture, and repository setup.

### Day 2 — Data Processing, ER Design and Baseline of VectorDB setup

**Goal:** Build a reliable data foundation and establish a baseline against which improvements can be measured.

**Issues to create:**

1. Implement data cleaning and preprocessing.
2. Perform exploratory data analysis and identify business-relevant patterns.
3. Create reusable feature engineering or data transformation modules.
4. Build a simple baseline model, ranking method, retrieval pipeline, or rule-based approach appropriate to the project.
5. Create ER for the SQL Clusters
6. Record baseline results and limitations.
7. Create a VectorDB instance using Milvus.

**Acceptance criteria:**

- Data transformations are reproducible.
- Key findings are supported by outputs or visualisations.
- The baseline has measurable evaluation results.
- No unsupported joins, target leakage, or undocumented synthetic assumptions are present.

**Day 2 deliverables:** Reproducible preprocessing, analysis, baseline implementation, and baseline evaluation report.

### Day 3 — Core ML and Decision Logic

**Goal:** Implement the main intelligence component and the deterministic rules that govern valid outcomes.

**Issues to create:**

1. Implement the selected ML, recommendation, classification, forecasting, or retrieval component.
2. Define business rules, eligibility checks, constraints, and validation logic.
3. Build a decision module that evaluates only valid candidate actions or outputs.
4. Implement structured outputs and meaningful error handling.
5. Compare the new approach with the baseline.

**Acceptance criteria:**

- The core component runs on prepared data.
- Evaluation metrics are documented.
- Business constraints are enforced independently of LLM-generated suggestions.
- Unsupported or infeasible decisions are rejected.

**Day 3 deliverables:** Working intelligence component, deterministic decision logic, and evaluation results.

### Day 4 — Backend and End-to-End Integration

**Goal:** Expose the core functionality through a usable application interface.

**Issues to create:**

1. Implement required FastAPI endpoints and Pydantic request/response schemas.
2. Integrate data processing, ML, retrieval, and decision modules.
3. Add persistence for necessary records, decisions, and audit events.
4. Implement input validation, configuration management, and structured logging.
5. Test the main workflow through API requests.

**Acceptance criteria:**

- The application starts using documented instructions.
- Required endpoints return valid, structured responses.
- Invalid inputs fail safely.
- The primary business workflow works end to end.

**Day 4 deliverables:** Working backend, API documentation, integration results, and updated README.

### Day 5 — Agentic Workflow and Guardrails

**Goal:** Orchestrate the workflow and demonstrate controlled, explainable decision-making.

**Issues to create:**

1. Implement the agentic workflow using the selected orchestration approach, if required.
2. Integrate approved tools and data sources with typed inputs and outputs.
3. Implement retrieval, context handling, or evidence collection where applicable.
4. Add guardrails for prompt injection, invalid tool arguments, data access, and unsupported claims.
5. Add human approval for consequential actions.
6. Build MCP Skills.
7. Implement fallback behaviour for LLM, retrieval, database, or tool failures.

**Acceptance criteria:**

- Workflow stages and transitions are traceable.
- Tool access is restricted to explicitly allowed operations.
- Decisions are grounded in available evidence and business rules.
- Consequential actions cannot bypass required approval.
- Failure paths produce safe and understandable responses.

**Day 5 deliverables:** Integrated workflow, guardrails, decision traces, and failure-handling demonstrations.

**Important:** Use an agentic framework only where it adds value. A deterministic workflow with a small number of well-defined agent stages is preferable to unnecessary multi-agent complexity.

### Day 6 — Testing, Evaluation and Troubleshooting

**Goal:** Verify correctness, security, reliability, and business relevance.

**Issues to create:**

1. Write unit tests for data transformations, models, and business rules.
2. Write integration tests for APIs, persistence, and workflow stages.
3. Test edge cases, missing data, malformed inputs, and unavailable dependencies.
4. Test prompt injection, unauthorised tool use, invalid approvals, and sensitive-data leakage where relevant.
5. Evaluate model or retrieval quality using appropriate metrics.
6. Fix defects and document known limitations.

**Acceptance criteria:**

- Tests run using documented commands.
- Critical business rules pass their test cases.
- Security tests demonstrate that unauthorised consequential actions are rejected.
- Model and retrieval metrics are reported honestly.
- Remaining defects and limitations are documented.

**Day 6 deliverables:** Test suite, evaluation report, defect fixes, security test evidence, and known-issues list.

### Day 7 — Final Demo and Handover

**Goal:** Demonstrate the complete solution and provide enough documentation for another developer to run it.

**Issues to create:**

1. Finalise the application and resolve critical defects.
2. Prepare a demonstration covering the business problem and end-to-end workflow.
3. Document architecture, setup, environment variables, APIs, and execution commands.
4. Prepare a final report containing the approach, results, limitations, and next steps.
5. Update the repository and attach evidence to Linear issues.
6. Conduct the final review and mark accepted issues as Done.

**Acceptance criteria:**

- The main workflow is demonstrated using a reproducible example.
- Setup instructions have been checked.
- Results and limitations are explained.
- The repository, documentation, and evidence are accessible to the reviewer.
- No critical issue is marked Done without validation.

**Day 7 deliverables:** Working demonstration, repository, final documentation, test report, evaluation summary, and handover.

---

## 4. Required Final Submission

Each candidate must provide:

1. Business problem statement and user stories.
2. Agentic System Flow Diagram.
3. Dataset source, data dictionary, preparation pipeline, and validation report.
4. Architecture diagram and repository folder structure.
5. Baseline and core model/decision implementation.
6. Working backend and frontend, if included in the assigned scope.
7. Agentic workflow, tool definitions, guardrails, and approval flow where applicable.
8. Unit and integration tests, with test results.
9. Evaluation metrics and a discussion of limitations.
10. README with setup, execution, API, and troubleshooting instructions.
11. Final demo and a summary of individual contributions.

## 5. Daily Reporting

At the end of each day, update Linear with:

- **Completed:** Issues finished and evidence attached.
- **In progress:** Work continuing and the next action.
- **Blocked:** Exact blocker, impact, and help required.
- **Next:** Planned tasks for the following day.

Every candidate should be able to explain what they implemented, why they chose the approach, which alternatives they considered, and how they validated the result.

## 6. Definition of Done

An issue is Done only when:

- Its acceptance criteria are satisfied.
- The relevant implementation or artifact exists.
- Evidence is attached or linked.
- Tests or validation have been performed where applicable.
- Documentation is updated where needed.
- Known limitations are recorded.

A project is complete when the end-to-end workflow is demonstrable, critical requirements are validated, and the final deliverables are available.

## 7. Mentor Review Checkpoints

- **Day 1:** Approve requirements, flow diagram, dataset preparation, and architecture before core implementation.
- **Day 3:** Review baseline results, model/decision logic, and business constraints.
- **Day 5:** Review the integrated workflow, tool permissions, guardrails, and approval behaviour.
- **Day 6:** Review test evidence, evaluation results, and unresolved defects.
- **Day 7:** Assess the demonstration, technical explanation, documentation, and individual contribution.

**Working principle:** Build a small, reliable, testable end-to-end solution first. Add complexity only when it solves a demonstrated business need.