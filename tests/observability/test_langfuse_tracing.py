from unittest.mock import MagicMock, patch
import pytest

from backend.app.observability.tracer import (
    clear_in_memory_traces,
    get_in_memory_traces,
    is_langfuse_configured,
    trace_agent_execution,
    trace_tool_execution,
)


@pytest.fixture(autouse=True)
def clean_traces():
    clear_in_memory_traces()
    yield
    clear_in_memory_traces()


def test_is_langfuse_configured_false_when_unset(monkeypatch):
    """When LANGFUSE keys are not set, is_langfuse_configured returns False."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert not is_langfuse_configured()


def test_trace_agent_execution_records_record():
    """Agent execution trace contains all necessary debug metadata."""
    record = trace_agent_execution(
        agent_name="reward_agent",
        input_state={"customer_id": 12347, "tier": "Gold"},
        output_state={"recommendations": ["SYN-REWARD-001"], "status": "FEASIBLE"},
        duration_ms=45.2,
        metadata={"model": "deterministic_baseline"},
        status="SUCCESS",
    )

    assert record["name"] == "reward_agent"
    assert record["status"] == "SUCCESS"
    assert record["duration_ms"] == 45.2
    assert record["input"]["customer_id"] == 12347
    assert len(record["trace_id"]) > 0

    all_traces = get_in_memory_traces(trace_type="agent")
    assert len(all_traces) == 1
    assert all_traces[0]["trace_id"] == record["trace_id"]


def test_trace_tool_execution_records_span():
    """Tool execution trace contains arguments, outputs, and span timing."""
    span = trace_tool_execution(
        tool_name="get_product_inventory",
        arguments={"product_id": "PROD-001"},
        result={"on_hand": 100, "reserved": 2},
        duration_ms=12.5,
        status="SUCCESS",
    )

    assert span["name"] == "get_product_inventory"
    assert span["arguments"] == {"product_id": "PROD-001"}
    assert span["result"]["on_hand"] == 100
    assert span["duration_ms"] == 12.5

    tool_traces = get_in_memory_traces(trace_type="tool")
    assert len(tool_traces) == 1
    assert tool_traces[0]["span_id"] == span["span_id"]


def test_trace_with_mocked_langfuse_client(monkeypatch):
    """When Langfuse is configured, traces and spans are forwarded to client."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")

    mock_client = MagicMock()

    with patch(
        "backend.app.observability.tracer.get_langfuse_client",
        return_value=mock_client,
    ):
        trace_agent_execution(
            agent_name="eligibility_agent",
            input_state={"customer_id": 12347},
            output_state={"eligible": True},
        )
        assert mock_client.trace.called

        trace_tool_execution(
            tool_name="get_customer_profile",
            arguments={"customer_id": 12347},
            result={"status": "active"},
        )
        assert mock_client.span.called

