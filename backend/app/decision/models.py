
from dataclasses import dataclass, field


@dataclass
class RewardCandidate:
    """Represents one reward option for a customer."""

    reward_id: str
    reward_name: str
    reward_type: str
    reward_value: float
    points_required: int
    campaign_id: str
    relevance_score: float = 0.0
    value_score: float = 0.0
    inventory_score: float = 0.0
    cost_penalty: float = 0.0

    eligible: bool = False
    reason_codes: list[str] = field(default_factory=list)


@dataclass
class RankedReward:
    """Represents a feasible reward with its ranking score."""

    candidate: RewardCandidate
    score: float
    rank: int | None = None


@dataclass
class RecommendationResult:
    """Represents the final reward recommendation."""

    customer_id: int
    recommendations: list[RankedReward] = field(default_factory=list)
    status: str = "SUCCESS"
    reason_codes: list[str] = field(default_factory=list)
