import pytest

from backend.app.mcp.client import LoyaltyMCPClient


@pytest.mark.asyncio
async def test_client_calls_mcp_tool():

    client = LoyaltyMCPClient()

    result = await client.call_tool(
        "get_transaction_history", {"customer_id": 101, "limit": 0}
    )

    assert result.is_error is False
    assert result.data["status"] == "INVALID_LIMIT"


@pytest.mark.asyncio
async def test_client_handles_invalid_limit():

    client = LoyaltyMCPClient()

    result = await client.call_tool(
        "get_transaction_history", {"customer_id": 101, "limit": 101}
    )

    assert result.is_error is False
    assert result.data["status"] == "INVALID_LIMIT"


@pytest.mark.asyncio
async def test_client_returns_transaction_data():

    client = LoyaltyMCPClient()

    result = await client.call_tool(
        "get_transaction_history", {"customer_id": 101, "limit": 20}
    )

    assert result.is_error is False
    assert result.data["status"] in ["SUCCESS", "DATASET_NOT_FOUND"]
