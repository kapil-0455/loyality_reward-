
import pytest
from fastmcp import Client

from backend.app.mcp.server import mcp


@pytest.mark.asyncio
async def test_mcp_tools_registered():

    async with Client(mcp) as client:
        tools = await client.list_tools()

        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "get_customer_profile",
            "get_transaction_history",
            "get_product_inventory",
            "get_campaign_details",
            "get_reward_details"
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names


@pytest.mark.asyncio
async def test_mcp_transaction_tool_validation():

    async with Client(mcp) as client:

        result = await client.call_tool(
            "get_transaction_history",
            arguments={
                "customer_id": 101,
                "limit": 0
            }
        )

        assert result.is_error is False
        assert result.data["status"] == "INVALID_LIMIT"


@pytest.mark.asyncio
async def test_mcp_transaction_tool_invalid_limit():

    async with Client(mcp) as client:

        result = await client.call_tool(
            "get_transaction_history",
            arguments={
                "customer_id": 101,
                "limit": 101
            }
        )

        assert result.is_error is False
        assert result.data["status"] == "INVALID_LIMIT"
