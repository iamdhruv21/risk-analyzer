from enum import Enum
from typing import Union, Literal
from pydantic import BaseModel, Field
from dataclasses import dataclass

class AssetClass(str, Enum):
    """Asset class enum matching risk analyzer format"""
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCKS = "stock"
    INDICES = "stock"  # Indices mapped to stock

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
    """Parsed trade signal - output format matches risk analyzer input"""
    asset: str
    assetClass: str  # lowercase: crypto, forex, stock, commodity
    type: SignalType
    price: float | None = None
    tp: PriceValue = None
    sl: PriceValue = None
    leverage: int | None = Field(default=1, ge=1, le=125)  # int, defaults to 1

@dataclass
class ParsingResult:
    """Result of signal parsing with metadata"""
    data: ParsedSignal | None
    latency_ms: float
    method: Literal["fast", "intelligence"]
    confidence: float
