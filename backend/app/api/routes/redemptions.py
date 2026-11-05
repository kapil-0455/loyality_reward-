
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.security import require_campaign_manager
from backend.app.api.schemas.redemption import (
    RedemptionRequest,
    RedemptionResponse,
)
from backend.app.db.session import SessionLocal
from backend.app.services.redemption_service import redeem_reward

router = APIRouter(
    prefix="/rewards",
    tags=["Redemptions"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/redemptions",
    response_model=RedemptionResponse
)
def create_redemption(
    request: RedemptionRequest,
    db: Session = Depends(get_db),
    manager: bool = Depends(require_campaign_manager),
):
    try:
        redemption = redeem_reward(db, request)

        return {
            "redemption_id": redemption.redemption_id,
            "customer_id": int(redemption.customer_id),
            "reward_id": redemption.reward_id,
            "status": redemption.redemption_status,
            "points_debited": redemption.points_debited,
            "message": "Reward redeemed successfully",
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while redeeming reward"
        )


@router.get("/redemptions/{redemption_id}")
def get_redemption(
    redemption_id: str,
    db: Session = Depends(get_db),
    manager: bool = Depends(require_campaign_manager),
):
    from backend.app.db.repositories.redemption_repository import (
        get_redemption_by_id,
    )

    redemption = get_redemption_by_id(db, redemption_id)

    if redemption is None:
        raise HTTPException(
            status_code=404,
            detail="Redemption not found"
        )

    return {
        "redemption_id": redemption.redemption_id,
        "approval_id": redemption.approval_id,
        "customer_id": int(redemption.customer_id),
        "reward_id": redemption.reward_id,
        "campaign_id": redemption.campaign_id,
        "status": redemption.redemption_status,
        "points_debited": redemption.points_debited,
        "reward_cost": float(redemption.reward_cost),
    }

