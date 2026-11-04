"""
Workflow runner with node-level execution tracing.
"""

from collections.abc import Mapping
from typing import Any


async def run_reward_workflow(graph, initial_state: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the compiled reward graph and collect a trace for every node.

    The trace contains node names, execution order, status, and safe error
    summaries. The accumulated result mirrors the state returned by ainvoke().
    """
    final_state = dict(initial_state)
    trace = []

    try:
        async for update in graph.astream(
            initial_state,
            stream_mode="updates",
        ):
            if not isinstance(update, Mapping):
                continue

            for node_name, node_update in update.items():
                if not isinstance(node_update, Mapping):
                    node_update = {}

                node_update = dict(node_update)
                final_state.update(node_update)

                trace.append({
                    "step": len(trace) + 1,
                    "node": node_name,
                    "status": node_update.get(
                        "status",
                        final_state.get("status", "UNKNOWN"),
                    ),
                    "error": node_update.get("error"),
                })

    except Exception as exc:
        # Do not expose raw exception text: it may contain connection details
        # or other sensitive configuration.
        error = f"Workflow execution failed ({type(exc).__name__})."
        final_state["status"] = "WORKFLOW_ERROR"
        final_state["error"] = error
        trace.append({
            "step": len(trace) + 1,
            "node": "workflow",
            "status": "WORKFLOW_ERROR",
            "error": error,
        })

    return {
        "result": final_state,
        "trace": trace,
    }
