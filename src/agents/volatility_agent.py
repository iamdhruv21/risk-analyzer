from typing import Dict, Any
from src.models.signal import TradeSignal, RiskContext

class VolatilityAgent:
    """Agent D: The Market Psychologist"""

    def analyze(self, signal: TradeSignal, context: RiskContext) -> Dict[str, Any]:
        if context.market_data is None and context.sentiment is None:
            return {
                "score": None,
                "reasoning": "Market data and sentiment data unavailable - cannot perform volatility analysis",
                "atr": None,
                "regime": None,
                "vix": None,
                "india_vix": None
            }

        market_data = context.market_data
        sentiment_data = context.sentiment

        atr = market_data.get("atr_14", 0) if market_data else 0
        regime = sentiment_data.get("market_regime") if sentiment_data else None
        vix = sentiment_data.get("vix") if sentiment_data else None
        india_vix = sentiment_data.get("india_vix") if sentiment_data else None

        score = 50
        reasons = []

        # 1. Market Regime Analysis
        if regime and regime == "bullish_expansion":
            score += 15
            reasons.append("Market in bullish expansion regime")
        elif regime == "bearish_capitulation":
            score -= 20
            reasons.append("Market in bearish capitulation regime")

        # 2. VIX Analysis (Global Volatility Index)
        # VIX Interpretation: <15 = Low volatility, 15-20 = Normal, 20-30 = Elevated, >30 = High fear
        if vix is not None:
            if vix < 15:
                # Low volatility - generally favorable for trading
                score += 10
                reasons.append(f"Low VIX ({vix:.1f}) - stable market conditions")
            elif 15 <= vix <= 20:
                # Normal volatility range
                score += 5
                reasons.append(f"Normal VIX ({vix:.1f}) - moderate volatility")
            elif 20 < vix <= 30:
                # Elevated volatility - caution needed
                score -= 10
                reasons.append(f"Elevated VIX ({vix:.1f}) - increased market volatility")
            elif vix > 30:
                # High fear - risky environment
                score -= 20
                reasons.append(f"High VIX ({vix:.1f}) - extreme market volatility")
        else:
            reasons.append("VIX data not available")

        # 3. India VIX Analysis (for Indian market exposure)
        # India VIX thresholds are similar to VIX: <15 = Low, 15-20 = Normal, 20-25 = Elevated, >25 = High
        if signal.assetClass == "stock" or signal.asset in ["NIFTY", "SENSEX", "INR"]:
            if india_vix is not None:
                if india_vix < 15:
                    score += 8
                    reasons.append(f"Low India VIX ({india_vix:.1f}) - stable Indian market")
                elif 15 <= india_vix <= 20:
                    score += 3
                    reasons.append(f"Normal India VIX ({india_vix:.1f})")
                elif 20 < india_vix <= 25:
                    score -= 8
                    reasons.append(f"Elevated India VIX ({india_vix:.1f}) - caution in Indian markets")
                elif india_vix > 25:
                    score -= 15
                    reasons.append(f"High India VIX ({india_vix:.1f}) - extreme volatility in Indian markets")
            else:
                reasons.append("India VIX data not available for Indian market asset")

        # 4. ATR Analysis - Stop Loss Distance Validation
        sl = signal.sl if isinstance(signal.sl, float) else signal.sl[0]
        sl_dist = abs(signal.price - sl)

        if atr > 0:
            atr_ratio = sl_dist / atr
            if atr_ratio < 1.0:
                score -= 15
                reasons.append(f"Volatility Warning: SL is within 1 ATR ({atr_ratio:.2f} ATR) - too tight")
            elif 1.0 <= atr_ratio < 1.5:
                score -= 5
                reasons.append(f"Marginal SL distance ({atr_ratio:.2f} ATR) - risk of premature stop-out")
            elif 1.5 <= atr_ratio <= 3.0:
                score += 15
                reasons.append(f"Conservative SL placement ({atr_ratio:.2f} ATR) - optimal range")
            elif atr_ratio > 3.0:
                score += 5
                reasons.append(f"Wide SL placement ({atr_ratio:.2f} ATR) - potentially large drawdown")
        else:
            reasons.append("ATR data not available")

        # 5. Cross-validation: VIX and ATR Alignment
        # If both VIX is high and ATR ratio is low, it's especially dangerous
        if vix is not None and vix > 25 and atr > 0:
            atr_ratio = sl_dist / atr
            if atr_ratio < 1.5:
                score -= 10
                reasons.append("Critical: High VIX combined with tight SL - elevated stop-out risk")

        return {
            "score": max(0, min(100, score)),
            "reasoning": "; ".join(reasons),
            "atr": atr,
            "regime": regime,
            "vix": vix,
            "india_vix": india_vix
        }
