from dataclasses import asdict, is_dataclass

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.schemas.recommendation import RecommendationRequest
from backend.app.db.session import SessionLocal
from backend.app.services.recommendation_service import get_recommendations

router = APIRouter(prefix="/rewards", tags=["Recommendations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/recommendations")
def create_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
):
    result = get_recommendations(
        db=db,
        customer_id=request.customer_id,
        purchase_value=request.purchase_value,
        evaluation_date=request.evaluation_date,
    )

    if isinstance(result, dict):
        if result.get("status") == "CUSTOMER_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Customer not found")
        return result

    if is_dataclass(result):
        return asdict(result)

    return result


@router.post("/agentic-recommendations")
async def create_agentic_recommendations(
    request: RecommendationRequest,
):
    """
    Run the six-agent LangGraph workflow and return its execution trace.

    This endpoint is separate from the existing deterministic endpoint so
    current API consumers are not affected.

    Note: The LangGraph workflow involves multiple LLM calls and may take
    60-180 seconds. On free-tier deployments, ensure your HTTP client has
    a timeout of at least 300 seconds.
    """
    import asyncio
    import traceback
    from backend.app.agents.graph_builder import build_reward_graph
    from backend.app.agents.graph_runner import run_reward_workflow
    from backend.app.mcp.client import LoyaltyMCPClient

    try:
        graph = build_reward_graph(
            mcp_client=LoyaltyMCPClient()
        )

        initial_state = {
            "request": "recommend a reward",
            "user_role": "customer",
            "customer_id": request.customer_id,
            "evaluation_date": request.evaluation_date.isoformat(),
            "purchase_value": float(request.purchase_value),
        }

        # Allow up to 5 minutes for the full multi-agent pipeline
        execution = await asyncio.wait_for(
            run_reward_workflow(graph, initial_state),
            timeout=270.0,
        )

        result = execution["result"]

        # Return only the public workflow result, not internal customer,
        # transaction, inventory, or campaign records.
        return {
            "customer_id": request.customer_id,
            "status": result.get("status", "UNKNOWN"),
            "recommendation_result": result.get("recommendation_result"),
            "final_response": result.get("final_response"),
            "trace": [
                {
                    "step": item["step"],
                    "node": item["node"],
                    "status": item["status"],
                    "error": (
                        "Node reported an error."
                        if item.get("error")
                        else None
                    ),
                }
                for item in execution["trace"]
            ],
        }
    except asyncio.TimeoutError:
        return {
            "customer_id": request.customer_id,
            "status": "TIMEOUT",
            "recommendation_result": None,
            "final_response": (
                "The agentic workflow timed out. "
                "Please retry — the server may have been cold-starting. "
                "Subsequent requests are significantly faster."
            ),
            "trace": [],
        }
    except Exception as exc:
        return {
            "customer_id": request.customer_id,
            "status": "WORKFLOW_EXCEPTION",
            "recommendation_result": None,
            "final_response": f"Workflow failed: {type(exc).__name__}: {str(exc)}",
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            "traceback": traceback.format_exc().splitlines()[-10:],
            "trace": [],
        }
