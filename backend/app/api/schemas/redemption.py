
from pydantic import BaseModel, Field


class RedemptionRequest(BaseModel):
    customer_id: int
    reward_id: str
    campaign_id: str
    idempotency_key: str = Field(min_length=1)


class RedemptionResponse(BaseModel):
    redemption_id: str
    customer_id: int
    reward_id: str
    status: str
    points_debited: int
    message: str | None = None
