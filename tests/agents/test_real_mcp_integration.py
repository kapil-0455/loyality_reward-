import pytest

from backend.app.agents.data_agent import run_data_agent
from backend.app.db.models import (
    CampaignBudget,
    CustomerLoyaltyProfile,
    RewardCatalogue,
)
from backend.app.db.session import SessionLocal
from backend.app.mcp.client import LoyaltyMCPClient


@pytest.mark.asyncio
async def test_real_mcp_postgres_integration():

    # Get real IDs from PostgreSQL
    db = SessionLocal()

    try:
        customer = db.query(CustomerLoyaltyProfile).first()
        reward = db.query(RewardCatalogue).first()

        if customer is None or reward is None:
            pytest.skip("Customer or reward data is missing in PostgreSQL")

        customer_id = int(customer.customer_id)
        reward_id = reward.reward_id
        campaign_id = reward.campaign_id

        campaign = (
            db.query(CampaignBudget)
            .filter(CampaignBudget.campaign_id == campaign_id)
            .first()
        )

        if campaign is None:
            pytest.skip("Campaign data is missing in PostgreSQL")

    finally:
        db.close()

    # Use the actual MCP client
    mcp_client = LoyaltyMCPClient()

    # 1. Customer profile
    customer_result = await run_data_agent(
        mcp_client, "customer", {"customer_id": customer_id}
    )

    assert customer_result["status"] == "SUCCESS"
    assert customer_result["data"]["customer_id"] is not None

    # 2. Transaction history
    transaction_result = await run_data_agent(
        mcp_client, "transactions", {"customer_id": customer_id}
    )

    assert transaction_result["status"] == "SUCCESS"

    # 3. Reward details
    reward_result = await run_data_agent(mcp_client, "reward", {"reward_id": reward_id})

    assert reward_result["status"] == "SUCCESS"

    # 4. Campaign details
    campaign_result = await run_data_agent(
        mcp_client, "campaign", {"campaign_id": campaign_id}
    )

    assert campaign_result["status"] == "SUCCESS"

    # 5. Reward-product mappings
    mapping_result = await run_data_agent(
        mcp_client, "reward_mappings", {"reward_id": reward_id}
    )

    assert mapping_result["status"] == "SUCCESS"
    assert isinstance(mapping_result["data"], list)

    # 6. Inventory for every mapped product
    for mapping in mapping_result["data"]:
        inventory_result = await run_data_agent(
            mcp_client, "inventory", {"product_id": mapping["product_id"]}
        )

        assert inventory_result["status"] == "SUCCESS"

        inventory = inventory_result["data"]

        assert inventory["product_id"] == mapping["product_id"]

    print("\nReal PostgreSQL + MCP integration successful.")
    print("Customer ID:", customer_id)
    print("Reward ID:", reward_id)
    print("Campaign ID:", campaign_id)
    print("Mapped products:", len(mapping_result["data"]))
