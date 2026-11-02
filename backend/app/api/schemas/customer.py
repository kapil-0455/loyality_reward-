
from pydantic import BaseModel, ConfigDict


class CustomerProfileResponse(BaseModel):
    customer_id: int
    loyalty_tier: str
    points_balance: int
    profile_status: str
    profile_created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)



class CustomerSegmentResponse(BaseModel):
    customer_id: int
    recency: int
    frequency: int
    monetary: float
    cluster: int
