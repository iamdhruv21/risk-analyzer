import json
import asyncio
from src.models.signal import TradeSignal, RiskContext
from src.services.context_aggregator import ContextAggregator

class RiskAnalyzer:
    def __init__(self):
        self.aggregator = ContextAggregator()

    async def analyze(self, result_json: dict):
        """
        Orchestrates Phase 1 of the Risk Analysis pipeline.
        - Layer 0: Signal Validation
        - Layer 1: Context Aggregation
        """
        print(f"--- Layer 0: Validating Signal ---")
        try:
            signal = TradeSignal(**result_json)
            print(f"Signal validated for {signal.asset} ({signal.type}) at {signal.price}")
        except Exception as e:
            print(f"Layer 0 Validation Failed: {e}")
            return {"decision": "REJECT", "reason": f"Invalid Signal: {str(e)}"}

        print(f"\n--- Layer 1: Aggregating Market Context ---")
        async with self.aggregator as aggregator:
            context = await aggregator.aggregate_all_context(signal)
            print(f"Context aggregated successfully.")
            
            # Task 1.3: Data Caching & Persistence (Placeholders)
            # In production, we would use Redis to cache these features:
            # await self.cache_context(signal.asset, context)
            
            # And PostgreSQL to log the initial signal and context:
            # await self.persist_signal_and_context(signal, context)
            
        return {
            "signal": signal.model_dump(),
            "context": context.model_dump(),
            "status": "PHASE_1_COMPLETE"
        }

    async def cache_context(self, asset: str, context: RiskContext):
        """Placeholder for Task 1.3: Redis caching"""
        pass

    async def persist_signal_and_context(self, signal: TradeSignal, context: RiskContext):
        """Placeholder for Task 1.3: PostgreSQL persistence"""
        pass

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
