
import pytest

from backend.app.agents.graph_builder import build_reward_graph
from backend.app.db.models import (
    CustomerLoyaltyProfile,
    RewardCatalogue,
)
from backend.app.db.session import SessionLocal
from backend.app.mcp.client import LoyaltyMCPClient


@pytest.mark.asyncio
async def test_real_langgraph_execution():

    # Get a customer and reward with matching tier and points
    db = SessionLocal()

    try:
        customer = (
            db.query(CustomerLoyaltyProfile)
            .filter(
                CustomerLoyaltyProfile.customer_id == 12348
            )
            .first()
        )

        reward = (
            db.query(RewardCatalogue)
            .filter(
                RewardCatalogue.reward_id == "SYN-REWARD-003"
            )
            .first()
        )

        if customer is None or reward is None:
            pytest.skip("Test customer or reward is missing")

        customer_id = int(customer.customer_id)
        reward_id = reward.reward_id
        campaign_id = reward.campaign_id

        assert customer.loyalty_tier in [
            tier.strip()
            for tier in (reward.eligible_tiers or "").split(",")
        ]

        assert customer.points_balance >= reward.points_required

    finally:
        db.close()

    # Create real MCP client
    mcp_client = LoyaltyMCPClient()

    # Build six-agent LangGraph
    graph = build_reward_graph(
        mcp_client=mcp_client
    )

    initial_state = {
        "request": "recommend a reward",
        "user_role": "customer",
        "customer_id": customer_id,
        "reward_id": reward_id,
        "campaign_id": campaign_id,
        "evaluation_date": "2026-11-04",
        "purchase_value": 0,
    }

    # Execute complete workflow
    result = await graph.ainvoke(initial_state)
    print("\nEligibility Results:")
    print(result.get("eligibility_results"))

    print("\nFeasible Candidates:")
    print(result.get("feasible_candidates"))

    # Basic workflow validation
    assert result["intent"] == "recommendation"

    assert (
        int(result["customer_data"]["customer_id"])
        == customer_id
    )

    assert result.get("status") in [
        "SUCCESS",
        "NO_FEASIBLE_REWARD"
    ]

    # Validate analytics
    analytics = result.get("analytics_result")

    assert analytics is not None
    assert analytics["status"] == "SUCCESS"

    assert (
        analytics["analytics"]["customer_id"]
        == str(customer_id)
    )

    # Validate recommendation result
    recommendation_result = result.get(
        "recommendation_result"
    )

    assert isinstance(recommendation_result, dict)

    recommendations = recommendation_result.get(
        "recommendations", []
    )

    assert isinstance(recommendations, list)

    if recommendation_result["status"] == "SUCCESS":

        assert recommendations

        feasible_ids = {
            candidate.reward_id
            for candidate in result.get(
                "feasible_candidates", []
            )
        }

        for recommendation in recommendations:

            candidate = recommendation["candidate"]

            # Recommended reward must be feasible
            assert candidate["reward_id"] in feasible_ids

            # Hard eligibility constraints must pass
            assert candidate["eligible"] is True
            assert candidate["reason_codes"] == []

            # Ranking must be valid
            assert recommendation["rank"] >= 1

    else:

        assert (
            recommendation_result["status"]
            == "NO_FEASIBLE_REWARD"
        )

        assert recommendations == []

    # Validate final response
    final_response = result.get("final_response")

    assert isinstance(final_response, str)
    assert final_response.strip()

    # Display workflow results
    print("\nCustomer ID:", customer_id)
    print("Reward ID:", reward_id)
    print("Campaign ID:", campaign_id)

    print("\nWorkflow Status:", result["status"])
    print("Analytics Status:", analytics["status"])

    print(
        "Recommendation Status:",
        recommendation_result["status"]
    )

    print("Recommendations:", recommendations)
    print("Final Response:", final_response)
