
import pytest

from backend.app.agents import graph_nodes
from backend.app.agents.graph_builder import build_reward_graph


class MockMCPClient:
    async def call_tool(self, tool_name, parameters):
        return {
            "status": "SUCCESS",
            "data": {"customer_id": 101}
        }


def setup_mock_agents(monkeypatch):

    monkeypatch.setattr(
        graph_nodes,
        "run_router_agent",
        lambda **kwargs: {
            "status": "SUCCESS",
            "intent": "recommendation",
            "route": "recommendation_agent"
        }
    )

    async def mock_data_agent(**kwargs):
        return {
            "status": "SUCCESS",
            "data": {"customer_id": 101}
        }

    monkeypatch.setattr(
        graph_nodes,
        "run_data_agent",
        mock_data_agent
    )

    monkeypatch.setattr(
        graph_nodes,
        "run_analytics_agent",
        lambda **kwargs: {
            "status": "SUCCESS",
            "analytics": {"cluster": 2}
        }
    )

    monkeypatch.setattr(
        graph_nodes,
        "run_eligibility_agent",
        lambda **kwargs: {
            "status": "SUCCESS",
            "eligible": True,
            "reason_codes": [],
            "candidate": {"reward_id": "R101"}
        }
    )

    monkeypatch.setattr(
        graph_nodes,
        "run_reward_agent",
        lambda **kwargs: [
            {"reward_id": "R101", "rank": 1}
        ]
    )

    monkeypatch.setattr(
        graph_nodes,
        "run_response_agent",
        lambda **kwargs: {
            "status": "SUCCESS",
            "response": "Your recommended reward is R101."
        }
    )


def get_initial_state():

    return {
        "request": "recommend a reward",
        "user_role": "customer",
        "customer_id": 101,
        "customer_context": {"customer_id": 101},
        "data_request_type": "customer",
        "data_parameters": {"customer_id": 101},
        "customer": {},
        "reward": {},
        "inventory": {},
        "campaign": {},
        "evaluation_date": "2026-11-04",
        "purchase_value": 0
    }


@pytest.mark.asyncio
async def test_complete_graph_execution(monkeypatch):

    setup_mock_agents(monkeypatch)

    graph = build_reward_graph(
        mcp_client=MockMCPClient()
    )

    result = await graph.ainvoke(get_initial_state())

    assert result["status"] == "SUCCESS"
    assert result["intent"] == "recommendation"
    assert result["recommendation_result"]["recommendations"][0]["reward_id"] == "R101"
    assert "R101" in result["final_response"]


@pytest.mark.asyncio
async def test_graph_stops_on_invalid_request(monkeypatch):

    monkeypatch.setattr(
        graph_nodes,
        "run_router_agent",
        lambda **kwargs: {
            "status": "UNSUPPORTED_INTENT",
            "intent": None,
            "route": None
        }
    )

    graph = build_reward_graph(
        mcp_client=MockMCPClient()
    )

    result = await graph.ainvoke(get_initial_state())

    assert result["status"] == "UNSUPPORTED_INTENT"
    assert "final_response" not in result


@pytest.mark.asyncio
async def test_graph_stops_when_data_agent_fails(monkeypatch):

    setup_mock_agents(monkeypatch)

    async def failing_data_agent(**kwargs):
        return {
            "status": "MCP_TOOL_ERROR",
            "data": None,
            "error": "MCP unavailable"
        }

    monkeypatch.setattr(
        graph_nodes,
        "run_data_agent",
        failing_data_agent
    )

    graph = build_reward_graph(
        mcp_client=MockMCPClient()
    )

    result = await graph.ainvoke(get_initial_state())

    assert result["status"] == "MCP_TOOL_ERROR"
    assert "final_response" not in result
