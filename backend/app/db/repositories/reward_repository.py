
from sqlalchemy.orm import Session

from backend.app.db.models import RewardCatalogue


def get_reward_by_id(db: Session, reward_id: str):
    return (
        db.query(RewardCatalogue)
        .filter(RewardCatalogue.reward_id == reward_id)
        .first()
    )


def get_all_rewards(db: Session):
    return db.query(RewardCatalogue).all()


def get_active_rewards(db: Session):
    return (
        db.query(RewardCatalogue)
        .filter(RewardCatalogue.status == "active")
        .all()
    )


def get_rewards_by_campaign(db: Session, campaign_id: str):
    return (
        db.query(RewardCatalogue)
        .filter(RewardCatalogue.campaign_id == campaign_id)
        .all()
    )
