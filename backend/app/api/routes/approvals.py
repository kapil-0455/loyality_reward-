from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.schemas.approval import (
    ApprovalRequest,
    ApprovalResponse,
)
from backend.app.db.session import SessionLocal
from backend.app.services.approval_service import approve_reward

router = APIRouter(
    prefix="/rewards",
    tags=["Approvals"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/approvals",
    response_model=ApprovalResponse
)
def create_approval(
    request: ApprovalRequest,
    db: Session = Depends(get_db),
):
    try:
        approval = approve_reward(db, request)

        return {
            "approval_id": approval.approval_id,
            "customer_id": int(approval.customer_id),
            "reward_id": approval.reward_id,
            "campaign_id": approval.campaign_id,
            "approval_status": approval.approval_status,
            "message": "Approval processed successfully",
            "reason_codes": [],
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing approval"
        )