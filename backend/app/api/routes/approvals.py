
from fastapi import APIRouter, HTTPException

from backend.app.api.schemas.approval import ApprovalRequest, ApprovalResponse

router = APIRouter(
    prefix="/rewards",
    tags=["Approvals"]
)


@router.post(
    "/approvals",
    response_model=ApprovalResponse
)
def approve_reward(request: ApprovalRequest):

    # Approval and database integration
    # will be implemented in the next steps.

    raise HTTPException(
        status_code=501,
        detail="Approval service is not connected yet"
    )
