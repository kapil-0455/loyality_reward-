import pytest

from backend.app.agents.data_agent import run_data_agent
from backend.app.mcp.client import LoyaltyMCPClient


@pytest.mark.asyncio
async def test_data_agent_with_mcp_client():

    client = LoyaltyMCPClient()

    result = await run_data_agent(client, "transactions", {"customer_id": 101})

    assert result["status"] in ["SUCCESS", "DATASET_NOT_FOUND"]

    if result["status"] == "SUCCESS":
        assert isinstance(result["data"], list)


@pytest.mark.asyncio
async def test_data_agent_invalid_tool_request():

    client = LoyaltyMCPClient()

    result = await run_data_agent(client, "unknown", {})

    assert result["status"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_data_agent_missing_parameter():

    client = LoyaltyMCPClient()

    result = await run_data_agent(client, "customer", {})

    assert result["status"] == "MISSING_PARAMETER"
