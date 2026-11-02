
from pydantic import BaseModel, Field


class ApprovalRequest(BaseModel):
    customer_id: int
    reward_id: str
    campaign_id: str
    approved: bool
    idempotency_key: str = Field(min_length=1)


class ApprovalResponse(BaseModel):
    customer_id: int
    reward_id: str
    approval_status: str
    message: str | None = None
