
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.schemas.customer import CustomerProfileResponse
from backend.app.db.repositories.customer_repository import get_customer_by_id
from backend.app.db.session import SessionLocal
from backend.app.services.segment_service import get_customer_segment
from backend.app.api.schemas.customer import CustomerSegmentResponse

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{customer_id}/profile", response_model=CustomerProfileResponse)
def get_customer_profile(
    customer_id: int,
    db: Session = Depends(get_db)
):
    customer = get_customer_by_id(db, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return {
        "customer_id": int(customer.customer_id),
        "loyalty_tier": customer.loyalty_tier,
        "points_balance": customer.points_balance,
        "profile_status": customer.profile_status,
        "profile_created_at": (
            customer.profile_created_at.isoformat()
            if customer.profile_created_at else None
        )
    }



@router.get(
    "/{customer_id}/segments",
    response_model=CustomerSegmentResponse
)
def get_customer_segments(customer_id: int):

    segment = get_customer_segment(customer_id)

    if segment is None:
        raise HTTPException(
            status_code=404,
            detail="Customer segment not found"
        )

    return segment
