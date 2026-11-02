
from sqlalchemy.orm import Session

from backend.app.db.models import CustomerLoyaltyProfile


def get_customer_by_id(db: Session, customer_id: int):
    return (
        db.query(CustomerLoyaltyProfile)
        .filter(
            CustomerLoyaltyProfile.customer_id == customer_id
        )
        .first()
    )


def get_all_customers(db: Session):
    return db.query(CustomerLoyaltyProfile).all()


def get_customer_count(db: Session):
    return db.query(CustomerLoyaltyProfile).count()
