
from unittest.mock import AsyncMock

import pytest

from backend.app.agents.data_agent import run_data_agent


@pytest.mark.asyncio
async def test_customer_data_retrieval():
    client = AsyncMock()
    client.call_tool.return_value = {"customer_id": 101}

    result = await run_data_agent(
        client,
        "customer",
        {"customer_id": 101}
    )

    assert result["status"] == "SUCCESS"
    client.call_tool.assert_awaited_once_with(
        "get_customer_profile",
        {"customer_id": 101}
    )


@pytest.mark.asyncio
async def test_inventory_data_retrieval():
    client = AsyncMock()
    client.call_tool.return_value = {"available_stock": 50}

    result = await run_data_agent(
        client,
        "inventory",
        {"product_id": "P101"}
    )

    assert result["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_missing_parameter():
    client = AsyncMock()

    result = await run_data_agent(
        client,
        "customer",
        {}
    )

    assert result["status"] == "MISSING_PARAMETER"
    client.call_tool.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_request_type():
    client = AsyncMock()

    result = await run_data_agent(
        client,
        "unknown",
        {}
    )

    assert result["status"] == "INVALID_REQUEST"
    client.call_tool.assert_not_called()


@pytest.mark.asyncio
async def test_mcp_tool_failure():
    client = AsyncMock()
    client.call_tool.side_effect = RuntimeError("MCP unavailable")

    result = await run_data_agent(
        client,
        "customer",
        {"customer_id": 101}
    )

    assert result["status"] == "MCP_TOOL_ERROR"
    assert result["data"] is None
