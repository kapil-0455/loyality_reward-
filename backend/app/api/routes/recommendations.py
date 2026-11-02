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
