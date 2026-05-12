from enum import Enum
from typing import Union, Literal
from pydantic import BaseModel
from dataclasses import dataclass

class AssetClass(str, Enum):
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    STOCKS = "STOCKS"
    INDICES = "INDICES"

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    LIMIT = "LIMIT"
    AMEND = "AMEND"

class PriceRange(BaseModel):
    min: float
    max: float

PriceValue = Union[float, list[float], PriceRange, None]

class ParsedSignal(BaseModel):
    """Parsed trade signal from text"""
    type: SignalType
    asset: str
    assetClass: AssetClass
    price: float | None = None
    leverage: float | None = None
    tp: PriceValue = None
    sl: PriceValue = None

@dataclass
class ParsingResult:
    """Result of signal parsing with metadata"""
    data: ParsedSignal | None
    latency_ms: float
    method: Literal["fast", "intelligence"]
    confidence: float
