from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class ApprovalRequest(BaseModel):
    customer_id: int
    reward_id: str
    campaign_id: str

    purchase_value: Decimal = Field(ge=0)
    evaluation_date: date

    approved: bool
    idempotency_key: str = Field(min_length=1)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: str
    customer_id: int
    reward_id: str
    campaign_id: str
    approval_status: str
    message: str | None = None
    reason_codes: list[str] = Field(default_factory=list)