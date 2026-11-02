
from sqlalchemy.orm import Session

from backend.app.db.models import CampaignBudget


def get_campaign_by_id(db: Session, campaign_id: str):
    return (
        db.query(CampaignBudget)
        .filter(CampaignBudget.campaign_id == campaign_id)
        .first()
    )


def get_all_campaigns(db: Session):
    return db.query(CampaignBudget).all()


def get_active_campaigns(db: Session):
    return (
        db.query(CampaignBudget)
        .filter(CampaignBudget.campaign_status == "active")
        .all()
    )


def get_available_budget(db: Session, campaign_id: str):
    campaign = get_campaign_by_id(db, campaign_id)

    if campaign is None:
        return None

    return (
        campaign.budget_limit
        - campaign.committed_amount
        - campaign.approved_amount
    )
