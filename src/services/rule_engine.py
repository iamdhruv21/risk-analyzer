from typing import Dict, Any, Optional
from src.models.signal import TradeSignal, RiskContext

class RuleEngine:
    def __init__(self):
        # Configurable thresholds
        self.MAX_RISK_PER_TRADE = 0.02  # 2%
        self.MIN_RR_RATIO = 1.5
        self.MAX_LEVERAGE_CRYPTO = 20
        self.MIN_SL_ATR_MULTIPLE = 0.5
        self.MAX_DAILY_DRAWDOWN = 0.05  # 5%

    def validate_fast_rules(self, signal: TradeSignal, context: RiskContext) -> Dict[str, Any]:
        """
        Executes Layer 2 Deterministic Gates.
        Returns a dict with 'pass': bool and 'reason': str if failed.
        """
        equity = context.portfolio_state.get("equity", 0.0)
        atr = context.market_data.get("atr_14", 0.0)
        daily_drawdown = context.portfolio_state.get("daily_drawdown", 0.0)

        # 1. Daily Drawdown Kill Switch
        if daily_drawdown >= self.MAX_DAILY_DRAWDOWN:
            return {"pass": False, "reason": f"Daily drawdown ({daily_drawdown*100}%) exceeds limit ({self.MAX_DAILY_DRAWDOWN*100}%)"}

        # 2. Risk/Reward (R:R) Validation
        # R:R = (|Entry - TP|) / (|Entry - SL|)
        # Assuming single TP/SL for simplicity in Layer 2
        tp = signal.tp if isinstance(signal.tp, float) else signal.tp[0]
        sl = signal.sl if isinstance(signal.sl, float) else signal.sl[0]
        
        tp_dist = abs(signal.price - tp)
        sl_dist = abs(signal.price - sl)
        
        if sl_dist == 0:
            return {"pass": False, "reason": "Stop Loss distance cannot be zero"}
            
        rr_ratio = tp_dist / sl_dist
        if rr_ratio < self.MIN_RR_RATIO:
            return {"pass": False, "reason": f"R:R ratio {rr_ratio:.2f} is below minimum {self.MIN_RR_RATIO}"}

        # 3. Leverage Cap
        if signal.assetClass == "crypto" and signal.leverage > self.MAX_LEVERAGE_CRYPTO:
            return {"pass": False, "reason": f"Leverage {signal.leverage}x exceeds crypto cap {self.MAX_LEVERAGE_CRYPTO}x"}

        # 4. Volatility Check (SL too tight?)
        if atr > 0:
            if sl_dist < (atr * self.MIN_SL_ATR_MULTIPLE):
                return {"pass": False, "reason": f"Stop Loss ({sl_dist}) is too tight for current ATR ({atr})"}

        # 5. Position Sizing Calculation
        # risk_amount = equity * 0.01 (Defaulting to 1% for calculation)
        risk_amount = equity * 0.01
        # position_size = risk_amount / sl_dist
        suggested_position_size = risk_amount / sl_dist if sl_dist > 0 else 0
        
        # Check if total risk exceeds MAX_RISK_PER_TRADE
        actual_risk_percent = (sl_dist * suggested_position_size) / equity if equity > 0 else 1.0
        if actual_risk_percent > self.MAX_RISK_PER_TRADE:
            # Adjust position size to fit max risk
            suggested_position_size = (equity * self.MAX_RISK_PER_TRADE) / sl_dist

        return {
            "pass": True,
            "metrics": {
                "rr_ratio": round(rr_ratio, 2),
                "suggested_position_size": round(suggested_position_size, 4),
                "risk_amount": round(risk_amount, 2),
                "sl_dist_atr_ratio": round(sl_dist / atr, 2) if atr > 0 else None
            }
        }
