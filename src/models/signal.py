from typing import Literal, Optional, Union, List
from pydantic import BaseModel, Field, field_validator

class TradeSignal(BaseModel):
    asset: str
    assetClass: Literal["crypto", "forex", "stock", "commodity"]
    type: Literal["BUY", "SELL"]
    price: float
    tp: Union[float, List[float]]  # Support for single TP or multiple TP levels
    sl: Union[float, List[float]]  # Support for single SL or multiple SL levels
    leverage: int = Field(ge=1, le=125)

    @field_validator("tp", "sl")
    @classmethod
    def validate_non_negative(cls, v):
        if isinstance(v, list):
            if any(x <= 0 for x in v):
                raise ValueError("TP/SL values must be positive")
        elif v <= 0:
            raise ValueError("TP/SL value must be positive")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return v

class RiskContext(BaseModel):
    """Placeholder for Layer 1 context data"""
    market_data: dict = {}
    news_data: list = []
    economic_calendar: list = []
    portfolio_state: dict = {}
    sentiment: dict = {}

class RiskAnalysisReport(BaseModel):
    """Layer 6: Final Structured Output"""
    signal: TradeSignal
    context: RiskContext
    metrics: dict
    agent_reports: dict
    synthesis: dict
    decision: str
    composite_score: Optional[float] = None
    rationale: str
    suggested_adjustments: Optional[dict] = None
    status: str = "COMPLETE"
    timestamp: str = Field(default_factory=lambda: "2026-05-01T12:00:00Z") # Mocked timestamp
