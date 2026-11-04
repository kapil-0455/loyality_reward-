"""
LangGraph Conditional Edges
Controls workflow routing between agent nodes.
"""


def route_after_router(state):
    """Route request after Router Agent."""

    if state.get("status") != "SUCCESS":
        return "end"

    return "data"


def route_after_data(state):
    """Continue only if Data Agent succeeds."""

    if state.get("status") != "SUCCESS":
        return "end"

    return "analytics"


def route_after_analytics(state):
    """Continue only if Analytics Agent succeeds."""

    if state.get("status") != "SUCCESS":
        return "end"

    return "eligibility"


def route_after_eligibility(state):
    """Send feasible rewards to Reward Agent."""

    if state.get("status") != "SUCCESS":
        return "end"

    if not state.get("feasible_candidates"):
        return "response"

    return "reward"


def route_after_reward(state):
    """Continue to response generation."""

    if state.get("status") not in ["SUCCESS", "NO_FEASIBLE_REWARD"]:
        return "end"

    return "response"


def route_after_response(state):
    """Finish the workflow."""

    return "end"
