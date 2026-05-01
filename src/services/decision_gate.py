from typing import Dict, Any, Literal

class DecisionGate:
    def __init__(self):
        # Minimum RR that even an LLM score cannot override
        self.HARD_MIN_RR = 1.2

    def make_final_decision(self, composite_score: float, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes Layer 5 Decision Gates.
        Maps composite score (0-100) to discrete actions with hard overrides.
        """
        rr_ratio = metrics.get("rr_ratio", 0.0)

        # 1. Hard Overrides (Regardless of AI Score)
        if rr_ratio < self.HARD_MIN_RR:
            return {
                "decision": "REJECT",
                "rationale": f"Hard override: Risk/Reward ratio {rr_ratio} is below absolute floor of {self.HARD_MIN_RR}."
            }

        # 2. Score-based mapping
        if composite_score >= 75:
            decision = "APPROVE"
        elif 50 <= composite_score < 75:
            decision = "ADJUST"
        elif 30 <= composite_score < 50:
            decision = "FLAG"
        else:
            decision = "REJECT"

        return {
            "decision": decision,
            "composite_score": composite_score,
            "rationale": f"Decision based on composite risk score of {composite_score}."
        }
