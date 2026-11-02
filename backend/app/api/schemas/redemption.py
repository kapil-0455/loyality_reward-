
from pydantic import BaseModel, Field, ConfigDict


class RedemptionRequest(BaseModel):
    approval_id: str
    customer_id: int
    reward_id: str
    campaign_id: str
    idempotency_key: str = Field(min_length=1)


class RedemptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    redemption_id: str
    customer_id: int
    reward_id: str
    status: str
    points_debited: int
    message: str | None = None
