import pytest

from backend.app.agents import graph_nodes
from backend.app.agents.graph_builder import build_reward_graph

MOCK_DATA = {
    "customer": {
        "customer_id": 101,
        "loyalty_tier": "Gold",
        "points_balance": 500,
        "profile_status": "active",
    },
    "transactions": [{"Invoice": "INV001"}],
    "active_rewards": [
        {
            "reward_id": "R101",
            "reward_name": "Discount",
            "reward_type": "discount",
            "reward_value": 100,
            "points_required": 200,
            "campaign_id": "C101",
            "status": "active",
        }
    ],
    "reward_mappings": [
        {
            "reward_id": "R101",
            "product_id": "P101",
            "minimum_stock_required": 1,
            "inventory_constraint_type": "minimum_stock",
        }
    ],
    "inventory": {
        "product_id": "P101",
        "on_hand_stock": 20,
        "reserved_stock": 2,
        "reorder_level": 5,
        "replenishment_date": None,
    },
    "campaign": {
        "campaign_id": "C101",
        "budget_limit": 10000,
        "committed_amount": 1000,
        "approved_amount": 500,
        "campaign_status": "active",
    },
}


class MockMCPClient:

    async def call_tool(self, tool_name, parameters):
        return {
            "status": "SUCCESS",
            "data": {"customer_id": 101},
        }


def setup_mock_agents(monkeypatch):

    monkeypatch.setattr(
        graph_nodes,
        "run_router_agent",
        lambda **kwargs: {
            "status": "SUCCESS",
            "intent": "recommendation",
            "route": "recommendation_agent",
        },
    )

    async def mock_data_agent(mcp_client, request_type, parameters):
        return {
            "status": "SUCCESS",
            "data": MOCK_DATA[request_type],
        }

    monkeypatch.setattr(
        graph_nodes,
        "run_data_agent",
        mock_data_agent,
    )

    monkeypatch.setattr(
        graph_nodes,
        "run_analytics_agent",
        lambda **kwargs: {
            "status": "SUCCESS",
            "analytics": {"cluster": 2},
        },
    )

    monkeypatch.setattr(
        graph_nodes,
        "run_eligibility_agent",
        lambda **kwargs: {
            "status": "SUCCESS",
            "eligible": True,
            "reason_codes": [],
            "candidate": {"reward_id": "R101"},
        },
    )

    monkeypatch.setattr(
        graph_nodes,
        "run_reward_agent",
        lambda **kwargs: [
            {"reward_id": "R101", "rank": 1}
        ],
    )

    monkeypatch.setattr(
        graph_nodes,
        "run_response_agent",
        lambda **kwargs: {
            "status": "SUCCESS",
            "response": "Your recommended reward is R101.",
        },
    )


def get_initial_state():

    return {
        "request": "recommend a reward",
        "user_role": "customer",
        "customer_id": 101,
        "evaluation_date": "2026-11-04",
        "purchase_value": 0,
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
    assert result["customer_data"]["customer_id"] == 101
    assert len(result["reward_data"]) == 1
    assert result["reward_data"][0]["reward"]["reward_id"] == "R101"

    assert (
        result["recommendation_result"]["recommendations"][0]["reward_id"]
        == "R101"
    )
    assert "R101" in result["final_response"]


@pytest.mark.asyncio
async def test_graph_stops_on_invalid_request(monkeypatch):

    monkeypatch.setattr(
        graph_nodes,
        "run_router_agent",
        lambda **kwargs: {
            "status": "UNSUPPORTED_INTENT",
            "intent": None,
            "route": None,
        },
    )

    graph = build_reward_graph(mcp_client=MockMCPClient())

    result = await graph.ainvoke(get_initial_state())

    assert result["status"] == "UNSUPPORTED_INTENT"
    assert "final_response" not in result


@pytest.mark.asyncio
async def test_graph_stops_when_data_agent_fails(monkeypatch):

    setup_mock_agents(monkeypatch)

    async def failing_data_agent(mcp_client, request_type, parameters):
        return {
            "status": "NOT_FOUND",
            "data": None,
        }

    monkeypatch.setattr(
        graph_nodes,
        "run_data_agent",
        failing_data_agent,
    )

    graph = build_reward_graph(mcp_client=MockMCPClient())

    result = await graph.ainvoke(get_initial_state())

    assert result["status"] == "NOT_FOUND"
    assert "final_response" not in result
