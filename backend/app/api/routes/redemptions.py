from fastapi import APIRouter, HTTPException

from backend.app.api.schemas.redemption import RedemptionRequest, RedemptionResponse

router = APIRouter(prefix="/rewards", tags=["Redemptions"])


@router.post("/redemptions", response_model=RedemptionResponse)
def redeem_reward(request: RedemptionRequest):

    # Actual redemption logic will be connected
    # with database and transaction service later.

    raise HTTPException(
        status_code=501, detail="Redemption service is not connected yet"
    )
@router.get("/redemptions/{redemption_id}")
def get_redemption(redemption_id: str):

    raise HTTPException(
        status_code=501,
        detail="Redemption lookup is not connected yet"
    )
