import json
import asyncio
from src.models.signal import TradeSignal, RiskContext
from src.services.context_aggregator import ContextAggregator
from src.services.rule_engine import RuleEngine
from src.services.decision_gate import DecisionGate

class RiskAnalyzer:
    def __init__(self):
        self.aggregator = ContextAggregator()
        self.rule_engine = RuleEngine()
        self.decision_gate = DecisionGate()

    async def analyze(self, result_json: dict):
        """
        Orchestrates the Risk Analysis pipeline.
        - Layer 0: Signal Validation
        - Layer 1: Context Aggregation
        - Layer 2: Fast Rule Engine
        - [PHASE 3/4]: Agents & LLM (Mocked for now)
        - Layer 5: Decision Gate
        """
        # Layer 0: Signal Validation
        print(f"--- Layer 0: Validating Signal ---")
        try:
            signal = TradeSignal(**result_json)
            print(f"Signal validated for {signal.asset}")
        except Exception as e:
            return {"decision": "REJECT", "reason": f"Invalid Signal: {str(e)}"}

        # Layer 1: Context Aggregation
        print(f"\n--- Layer 1: Aggregating Market Context ---")
        async with self.aggregator as aggregator:
            context = await aggregator.aggregate_all_context(signal)
            print(f"Context aggregated from {context.market_data.get('source')}")

        # Layer 2: Fast Rule Engine (Deterministic Gate)
        print(f"\n--- Layer 2: Executing Fast Rules ---")
        rule_results = self.rule_engine.validate_fast_rules(signal, context)
        if not rule_results["pass"]:
            print(f"Layer 2 REJECT: {rule_results['reason']}")
            return {
                "decision": "REJECT",
                "reason": rule_results["reason"],
                "stage": "LAYER_2_FAST_RULE"
            }
        
        metrics = rule_results["metrics"]
        print(f"Fast rules passed. R:R: {metrics['rr_ratio']}, Position Size: {metrics['suggested_position_size']}")

        # Phase 3 & 4: (Mocked until implemented)
        print(f"\n--- Phase 3 & 4: (Placeholder for Agents & LLM) ---")
        mock_composite_score = 80 # Placeholder for Phase 4 output

        # Layer 5: Decision Gate (Final Override)
        print(f"--- Layer 5: Decision Gate ---")
        final_decision = self.decision_gate.make_final_decision(mock_composite_score, metrics)
        
        return {
            "signal": signal.model_dump(),
            "context": context.model_dump(),
            "metrics": metrics,
            "analysis": final_decision,
            "status": "PHASE_2_COMPLETE"
        }

async def run_example(result_json):
    analyzer = RiskAnalyzer()
    analysis_result = await analyzer.analyze(result_json)
    print("\n--- Final Output (Phase 1) ---")
    print(json.dumps(analysis_result, indent=2))

if __name__ == "__main__":
    # Sample input as requested
    resultJson = {
        "asset": "BTC",
        "assetClass": "crypto",
        "type": "BUY",
        "price": 65000,
        "tp": 68000,
        "sl": 63500,
        "leverage": 10
    }
    
    asyncio.run(run_example(resultJson))
