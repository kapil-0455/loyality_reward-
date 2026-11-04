import pytest

from backend.app.agents.graph_runner import run_reward_workflow


class MockGraph:

    def __init__(self, updates):
        self.updates = updates

    async def astream(self, initial_state, stream_mode):
        assert stream_mode == "updates"

        for update in self.updates:
            yield update


@pytest.mark.asyncio
async def test_runner_collects_node_trace_and_final_state():

    graph = MockGraph([
        {"router": {"intent": "recommendation", "status": "SUCCESS"}},
        {"data": {"customer_data": {"customer_id": 101}, "status": "SUCCESS"}},
        {"analytics": {"analytics_result": {"status": "SUCCESS"}, "status": "SUCCESS"}},
        {"eligibility": {"feasible_candidates": [], "status": "SUCCESS"}},
        {"reward": {"recommendation_result": {
            "status": "NO_FEASIBLE_REWARD",
            "recommendations": [],
        }, "status": "NO_FEASIBLE_REWARD"}},
        {"response": {"final_response": "No eligible reward found.", "status": "SUCCESS"}},
    ])

    output = await run_reward_workflow(
        graph,
        {"request": "recommend a reward", "customer_id": 101},
    )

    assert output["result"]["customer_id"] == 101
    assert output["result"]["final_response"] == "No eligible reward found."
    assert output["result"]["status"] == "SUCCESS"

    assert [item["node"] for item in output["trace"]] == [
        "router",
        "data",
        "analytics",
        "eligibility",
        "reward",
        "response",
    ]

    assert output["trace"][4]["status"] == "NO_FEASIBLE_REWARD"
    assert output["trace"][5]["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_runner_records_failure_and_preserves_trace():

    graph = MockGraph([
        {"router": {"intent": None, "status": "SUCCESS"}},
        {"data": {"status": "DATABASE_ERROR", "error": "Database unavailable"}},
    ])

    output = await run_reward_workflow(graph, {"customer_id": 101})

    assert output["result"]["status"] == "DATABASE_ERROR"
    assert output["trace"][-1]["node"] == "data"
    assert output["trace"][-1]["status"] == "DATABASE_ERROR"
    assert output["trace"][-1]["error"] == "Database unavailable"


class FailingGraph:

    async def astream(self, initial_state, stream_mode):
        yield {"router": {"status": "SUCCESS"}}
        raise RuntimeError("secret connection string must not leak")


@pytest.mark.asyncio
async def test_runner_handles_unexpected_workflow_exception_safely():

    output = await run_reward_workflow(FailingGraph(), {"customer_id": 101})

    assert output["result"]["status"] == "WORKFLOW_ERROR"
    assert "RuntimeError" in output["result"]["error"]
    assert "secret connection string" not in output["result"]["error"]
    assert output["trace"][-1]["node"] == "workflow"
