from typing import Dict, Any
from src.models.signal import TradeSignal, RiskContext

class VolatilityAgent:
    """Agent D: The Market Psychologist"""
    
    def analyze(self, signal: TradeSignal, context: RiskContext) -> Dict[str, Any]:
        market_data = context.market_data
        atr = market_data.get("atr_14", 0)
        regime = context.sentiment.get("market_regime", "neutral")
        
        score = 50
        reasons = []

        if regime == "bullish_expansion":
            score += 15
            reasons.append("Market in bullish expansion regime")
        elif regime == "bearish_capitulation":
            score -= 20
            reasons.append("Market in bearish capitulation regime")

        # ATR analysis
        sl = signal.sl if isinstance(signal.sl, float) else signal.sl[0]
        sl_dist = abs(signal.price - sl)
        
        if atr > 0:
            atr_ratio = sl_dist / atr
            if atr_ratio < 1.0:
                score -= 10
                reasons.append(f"Volatility Warning: SL is within 1 ATR ({atr_ratio:.2f} ATR)")
            elif 1.5 <= atr_ratio <= 3.0:
                score += 15
                reasons.append(f"Conservative SL placement ({atr_ratio:.2f} ATR)")

        return {
            "score": max(0, min(100, score)),
            "reasoning": "; ".join(reasons),
            "atr": atr,
            "regime": regime
        }
