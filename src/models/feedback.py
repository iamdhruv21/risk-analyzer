from typing import Literal, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class TradeFeedback(BaseModel):
    """Human feedback on a completed trade analysis"""
    trade_id: str
    feedback_id: str = Field(default_factory=lambda: f"fb_{int(datetime.utcnow().timestamp() * 1000)}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Outcome
    actual_outcome: Literal["SUCCESS", "FAILURE", "PARTIAL_SUCCESS", "NOT_EXECUTED", "PENDING"]
    outcome_reason: str

    # Decision quality assessment
    was_decision_correct: bool
    decision_quality_score: int = Field(ge=1, le=10, description="1=Very Poor, 10=Excellent")

    # Detailed feedback
    what_went_right: Optional[str] = None
    what_went_wrong: Optional[str] = None
    missed_factors: Optional[List[str]] = None

    # Suggested corrections
    should_have_been: Optional[Literal["APPROVE", "ADJUST", "FLAG", "REJECT"]] = None
    reasoning_corrections: Optional[str] = None

    # Agent-specific feedback
    technical_agent_accuracy: Optional[int] = Field(None, ge=1, le=10)
    sentiment_agent_accuracy: Optional[int] = Field(None, ge=1, le=10)
    metrics_agent_accuracy: Optional[int] = Field(None, ge=1, le=10)
    volatility_agent_accuracy: Optional[int] = Field(None, ge=1, le=10)

    # Market context at resolution time
    actual_price_movement: Optional[float] = None
    tp_hit: Optional[bool] = None
    sl_hit: Optional[bool] = None
    max_drawdown_percent: Optional[float] = None
    max_profit_percent: Optional[float] = None

    # Learning signals for RL
    reward_signal: float = Field(ge=-1.0, le=1.0, description="-1=Very Bad, 0=Neutral, 1=Very Good")
    confidence: float = Field(ge=0.0, le=1.0, description="Feedback provider's confidence")

    # Metadata
    feedback_provider: str
    notes: Optional[str] = None

    @field_validator("outcome_reason", "what_went_right", "what_went_wrong")
    @classmethod
    def validate_non_empty_string(cls, v):
        if v is not None and isinstance(v, str) and len(v.strip()) == 0:
            raise ValueError("String fields cannot be empty if provided")
        return v


class FeedbackQuery(BaseModel):
    """Query parameters for retrieving feedback"""
    trade_ids: Optional[List[str]] = None
    decision: Optional[Literal["APPROVE", "ADJUST", "FLAG", "REJECT"]] = None
    actual_outcome: Optional[Literal["SUCCESS", "FAILURE", "PARTIAL_SUCCESS", "NOT_EXECUTED", "PENDING"]] = None
    min_quality_score: Optional[int] = Field(None, ge=1, le=10)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)


class FeedbackSummary(BaseModel):
    """Aggregated feedback statistics"""
    total_feedbacks: int
    avg_decision_quality: float
    avg_reward_signal: float
    outcome_distribution: dict
    decision_accuracy: dict
    agent_accuracy_avg: dict
    top_missed_factors: List[dict]
