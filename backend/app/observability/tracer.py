"""
Observability and Trace Logging
Provides tracing for agent nodes, decision layers, and MCP tools
with Langfuse integration and in-memory trace verification.
"""

import os
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

_in_memory_traces: list[dict[str, Any]] = []


def is_langfuse_configured() -> bool:
    """Check if Langfuse credentials are configured."""
    return bool(
        os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
    )


def get_langfuse_client():
    """Return Langfuse client if configured, otherwise None."""
    if not is_langfuse_configured():
        return None

    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except ImportError :  
        return None


def trace_agent_execution(
    agent_name: str,
    input_state: dict[str, Any],
    output_state: dict[str, Any],
    duration_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
    status: str = "SUCCESS",
    error_message: str | None = None,
) -> dict[str, Any]:
    """
    Record an agent execution trace.
    Stores the trace in-memory and emits to Langfuse if configured.
    """
    trace_id = str(uuid4())
    record = {
        "trace_id": trace_id,
        "type": "agent",
        "name": agent_name,
        "input": input_state,
        "output": output_state,
        "duration_ms": duration_ms,
        "metadata": metadata or {},
        "status": status,
        "error_message": error_message,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    _in_memory_traces.append(record)

    client = get_langfuse_client()
    if client is not None:
        try:
            client.trace(
                id=trace_id,
                name=f"agent:{agent_name}",
                input=input_state,
                output=output_state,
                metadata=metadata,
                tags=[agent_name, status],
            )
        except Exception as e :  # noqa: BLE001
            pass

    return record


def trace_tool_execution(
    tool_name: str,
    arguments: dict[str, Any],
    result: Any,
    duration_ms: float | None = None,
    status: str = "SUCCESS",
    error_message: str | None = None,
) -> dict[str, Any]:
    """
    Record an MCP or system tool execution span.
    """
    span_id = str(uuid4())
    record = {
        "span_id": span_id,
        "type": "tool",
        "name": tool_name,
        "arguments": arguments,
        "result": result,
        "duration_ms": duration_ms,
        "status": status,
        "error_message": error_message,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    _in_memory_traces.append(record)

    client = get_langfuse_client()
    if client is not None:
        try:
            client.span(
                id=span_id,
                name=f"tool:{tool_name}",
                input=arguments,
                output=result,
            )
        except Exception:  # noqa: BLE001
            pass

    return record


def get_in_memory_traces(trace_type: str | None = None) -> list[dict[str, Any]]:
    """Return recorded traces, optionally filtered by type ('agent' or 'tool')."""
    if trace_type:
        return [t for t in _in_memory_traces if t.get("type") == trace_type]
    return list(_in_memory_traces)


def clear_in_memory_traces() -> None:
    """Clear all in-memory traces."""
    _in_memory_traces.clear()
