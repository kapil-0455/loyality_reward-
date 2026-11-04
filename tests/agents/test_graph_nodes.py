import pytest

from backend.app.agents import graph_nodes


@pytest.mark.asyncio
async def test_data_node_fetches_and_normalizes_data(monkeypatch):

    mock_data = {
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

    async def mock_data_agent(mcp_client, request_type, parameters):
        return {
            "status": "SUCCESS",
            "data": mock_data[request_type],
        }

    monkeypatch.setattr(
        graph_nodes,
        "run_data_agent",
        mock_data_agent,
    )

    nodes = graph_nodes.build_agent_nodes(mcp_client=None)

    result = await nodes["data"]({"customer_id": 101})

    assert result["status"] == "SUCCESS"
    assert result["customer_data"]["customer_id"] == 101
    assert result["transaction_data"] == mock_data["transactions"]

    assert len(result["reward_data"]) == 1
    reward_context = result["reward_data"][0]

    assert reward_context["reward"]["reward_id"] == "R101"
    assert reward_context["reward"]["reward_cost"] == 100
    assert reward_context["inventory"][0]["product_id"] == "P101"
    assert reward_context["inventory"][0]["minimum_stock_level"] == 5
    assert reward_context["inventory"][0]["required_quantity"] == 1
    assert reward_context["campaign"]["status"] == "active"

    # Legacy single-reward fields remain available.
    assert result["reward"]["reward_id"] == "R101"
    assert result["inventory"][0]["product_id"] == "P101"
    assert result["campaign"]["status"] == "active"


@pytest.mark.asyncio
async def test_data_node_stops_on_mcp_failure(monkeypatch):

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

    nodes = graph_nodes.build_agent_nodes(mcp_client=None)

    result = await nodes["data"]({"customer_id": 999})

    assert result["status"] == "NOT_FOUND"
    assert result.get("customer_data") is None
    assert result.get("inventory", []) == []
