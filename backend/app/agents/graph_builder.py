
"""
LangGraph Builder
Connects all six agents into one workflow.
"""

from langgraph.graph import END, StateGraph

from backend.app.agents.graph_edges import (
    route_after_analytics,
    route_after_data,
    route_after_eligibility,
    route_after_reward,
    route_after_router,
)
from backend.app.agents.graph_nodes import build_agent_nodes
from backend.app.agents.graph_state import RewardGraphState


def build_reward_graph(mcp_client, llm=None, laya_router=None):

    # Create all agent nodes
    nodes = build_agent_nodes(
        mcp_client=mcp_client,
        llm=llm,
        laya_router=laya_router
    )

    # Initialize StateGraph
    workflow = StateGraph(RewardGraphState)

    # Register six agents
    workflow.add_node("router", nodes["router"])
    workflow.add_node("data", nodes["data"])
    workflow.add_node("analytics", nodes["analytics"])
    workflow.add_node("eligibility", nodes["eligibility"])
    workflow.add_node("reward", nodes["reward"])
    workflow.add_node("response", nodes["response"])

    # Starting point
    workflow.set_entry_point("router")

    # Conditional routing
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "data": "data",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "data",
        route_after_data,
        {
            "analytics": "analytics",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "analytics",
        route_after_analytics,
        {
            "eligibility": "eligibility",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "eligibility",
        route_after_eligibility,
        {
            "reward": "reward",
            "response": "response",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "reward",
        route_after_reward,
        {
            "response": "response",
            "end": END
        }
    )

    # Final response
    workflow.add_edge("response", END)

    # Compile graph
    return workflow.compile()
