"""
Shared State for Loyalty Reward LangGraph Workflow.
"""

from typing import Any, TypedDict


class RewardGraphState(TypedDict, total=False):
    # Request and routing
    request: str
    user_role: str
    intent: str
    route: str

    # Customer information
    customer_id: int
    customer_context: dict[str, Any]
    customer_data: Any

    # Data Agent inputs
    data_request_type: str
    data_parameters: dict[str, Any]

    # Analytics
    analytics_result: dict[str, Any]

    # Eligibility Agent inputs
    customer: dict[str, Any]
    reward: dict[str, Any]
    inventory: dict[str, Any]
    campaign: dict[str, Any]
    evaluation_date: str
    purchase_value: float

    # Eligibility output
    eligibility_results: list[Any]
    feasible_candidates: list[Any]

    # Reward Agent
    recommendation_result: Any

    # Response Agent
    final_response: str

    # MCP
    mcp_results: dict[str, Any]

    # Workflow status
    status: str
    error: str
    errors: list[str]

    # Approval reference
    approval_id: str
