
from sqlalchemy.orm import Session

from backend.app.db.models import RewardLedger


def get_redemption_by_id(db: Session, redemption_id: str):
    return (
        db.query(RewardLedger)
        .filter(RewardLedger.redemption_id == redemption_id)
        .first()
    )


def get_redemption_by_idempotency_key(
    db: Session,
    idempotency_key: str
):
    return (
        db.query(RewardLedger)
        .filter(
            RewardLedger.idempotency_key == idempotency_key
        )
        .first()
    )


def create_redemption(db: Session, redemption_data: dict):
    redemption = RewardLedger(**redemption_data)

    db.add(redemption)
    db.flush()

    return redemption


def get_customer_redemptions(db: Session, customer_id: int):
    return (
        db.query(RewardLedger)
        .filter(RewardLedger.customer_id == customer_id)
        .all()
    )
