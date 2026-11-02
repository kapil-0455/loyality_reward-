
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    customer_id: int
    purchase_value: Decimal = Field(ge=0)
    evaluation_date: date


class RecommendedReward(BaseModel):
    reward_id: str
    reward_name: str
    reward_type: str
    reward_value: Decimal
    points_required: int
    score: float
    rank: int


class RecommendationResponse(BaseModel):
    customer_id: int
    status: str
    recommendations: list[RecommendedReward]
    message: str | None = None
