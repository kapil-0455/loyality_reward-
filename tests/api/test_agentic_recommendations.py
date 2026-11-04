from datetime import date
from unittest.mock import AsyncMock

import pytest

from backend.app.api.schemas.recommendation import RecommendationRequest
from backend.app.api.routes import recommendations


@pytest.mark.asyncio
async def test_agentic_recommendation_endpoint_returns_trace(monkeypatch):

    class MockGraph:
        pass

    monkeypatch.setattr(
        "backend.app.agents.graph_builder.build_reward_graph",
        lambda mcp_client: MockGraph(),
    )

    expected = {
        "result": {
            "status": "SUCCESS",
            "recommendation_result": {
                "status": "SUCCESS",
                "recommendations": [],
            },
            "final_response": "Recommendation explanation.",
            "customer_data": {"private": "must not be returned"},
        },
        "trace": [
            {
                "step": 1,
                "node": "router",
                "status": "SUCCESS",
                "error": None,
            },
            {
                "step": 2,
                "node": "data",
                "status": "DATABASE_ERROR",
                "error": "database connection details",
            },
        ],
    }

    runner = AsyncMock(return_value=expected)
    monkeypatch.setattr(
        "backend.app.agents.graph_runner.run_reward_workflow",
        runner,
    )

    monkeypatch.setattr(
        "backend.app.mcp.client.LoyaltyMCPClient",
        lambda: "mock-mcp-client",
    )

    request = RecommendationRequest(
        customer_id=101,
        purchase_value=0,
        evaluation_date=date(2026, 11, 4),
    )

    response = await recommendations.create_agentic_recommendations(request)

    assert response["status"] == "SUCCESS"
    assert response["customer_id"] == 101
    assert response["final_response"] == "Recommendation explanation."
    assert "customer_data" not in response
    assert response["trace"][1]["error"] == "Node reported an error."
    assert "database connection details" not in str(response)


@pytest.mark.asyncio
async def test_agentic_endpoint_passes_request_context_to_runner(monkeypatch):

    captured = {}

    class MockGraph:
        pass

    monkeypatch.setattr(
        "backend.app.agents.graph_builder.build_reward_graph",
        lambda mcp_client: MockGraph(),
    )

    async def fake_runner(graph, initial_state):
        captured.update(initial_state)
        return {
            "result": {"status": "DATASET_NOT_FOUND"},
            "trace": [],
        }

    monkeypatch.setattr(
        "backend.app.agents.graph_runner.run_reward_workflow",
        fake_runner,
    )
    monkeypatch.setattr(
        "backend.app.mcp.client.LoyaltyMCPClient",
        lambda: "mock-mcp-client",
    )

    request = RecommendationRequest(
        customer_id=202,
        purchase_value=125.50,
        evaluation_date=date(2026, 11, 5),
    )

    response = await recommendations.create_agentic_recommendations(request)

    assert captured["customer_id"] == 202
    assert captured["purchase_value"] == 125.50
    assert captured["evaluation_date"] == "2026-11-05"
    assert response["status"] == "DATASET_NOT_FOUND"
