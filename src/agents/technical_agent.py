import pandas as pd
import pandas_ta as ta
from typing import Dict, Any
from src.models.signal import TradeSignal, RiskContext

class TechnicalAgent:
    """Agent A: The Chart Reader"""
    
    def analyze(self, signal: TradeSignal, context: RiskContext) -> Dict[str, Any]:
        if context.market_data is None:
            return {
                "score": None,
                "reasoning": "Market data unavailable - cannot perform technical analysis",
                "indicators": None
            }

        ohlcv = context.market_data.get("ohlcv", [])
        if not ohlcv or len(ohlcv) < 14:
            return {
                "score": None,
                "reasoning": "Insufficient OHLCV data for technical analysis (minimum 14 bars required)",
                "indicators": None
            }

        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Indicators
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        df.ta.adx(append=True)
        
        last_row = df.iloc[-1]
        rsi = last_row.get('RSI_14', 50)
        ema_50 = last_row.get('EMA_50', 0)
        ema_200 = last_row.get('EMA_200', 0)
        adx = last_row.get('ADX_14', 0)
        
        score = 50
        reasons = []

        # Trend Alignment
        if signal.type == "BUY":
            if last_row['close'] > ema_50:
                score += 15
                reasons.append("Price above EMA 50 (Bullish)")
            if ema_50 > ema_200:
                score += 10
                reasons.append("EMA 50 > EMA 200 (Golden Cross potential)")
        else: # SELL
            if last_row['close'] < ema_50:
                score += 15
                reasons.append("Price below EMA 50 (Bearish)")

        # RSI Momentum
        if signal.type == "BUY" and rsi < 30:
            score += 10
            reasons.append("RSI Oversold (Possible bounce)")
        elif signal.type == "BUY" and rsi > 70:
            score -= 10
            reasons.append("RSI Overbought (Risk of pullback)")

        # ADX Strength
        if adx > 25:
            score += 5
            reasons.append(f"Strong trend (ADX: {adx:.1f})")

        return {
            "score": max(0, min(100, score)),
            "reasoning": "; ".join(reasons),
            "indicators": {
                "rsi": round(rsi, 2),
                "adx": round(adx, 2),
                "trend": "bullish" if last_row['close'] > ema_50 else "bearish"
            }
        }
