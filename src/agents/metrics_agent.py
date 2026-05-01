import numpy as np
from typing import Dict, Any
from src.models.signal import TradeSignal, RiskContext

class MetricsAgent:
    """Agent C: The Risk Quant"""
    
    def analyze(self, signal: TradeSignal, context: RiskContext) -> Dict[str, Any]:
        # Recalculate and validate RR
        tp = signal.tp if isinstance(signal.tp, float) else signal.tp[0]
        sl = signal.sl if isinstance(signal.sl, float) else signal.sl[0]
        
        tp_dist = abs(signal.price - tp)
        sl_dist = abs(signal.price - sl)
        rr_ratio = tp_dist / sl_dist if sl_dist > 0 else 0
        
        score = 50
        reasons = []

        if rr_ratio >= 2.0:
            score += 20
            reasons.append(f"Excellent R:R ratio ({rr_ratio:.2f})")
        elif rr_ratio >= 1.5:
            score += 10
            reasons.append(f"Acceptable R:R ratio ({rr_ratio:.2f})")

        # Liquidation check (very basic)
        # For 10x leverage, 10% move against you is liquidation
        liq_threshold = 1.0 / signal.leverage
        sl_percent = sl_dist / signal.price
        
        if sl_percent > (liq_threshold * 0.8):
            score -= 30
            reasons.append(f"High liquidation risk: SL ({sl_percent*100:.1f}%) too close to liquidation ({liq_threshold*100:.1f}%)")

        return {
            "score": max(0, min(100, score)),
            "reasoning": "; ".join(reasons),
            "rr_ratio": round(rr_ratio, 2),
            "liquidation_risk": "high" if sl_percent > (liq_threshold * 0.8) else "low"
        }
