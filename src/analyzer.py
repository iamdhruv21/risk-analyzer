import json
import asyncio
from src.models.signal import TradeSignal, RiskContext, RiskAnalysisReport
from src.services.context_aggregator import ContextAggregator
from src.services.rule_engine import RuleEngine
from src.services.decision_gate import DecisionGate
from src.agents.technical_agent import TechnicalAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.metrics_agent import MetricsAgent
from src.agents.volatility_agent import VolatilityAgent
from src.agents.synthesis_agent import RiskSynthesisAgent
from src.services.audit_logger import AuditLogger

class RiskAnalyzer:
    def __init__(self, source_filename: str = None):
        self.aggregator = ContextAggregator()
        self.rule_engine = RuleEngine()
        self.decision_gate = DecisionGate()

        self.tech_agent = TechnicalAgent()
        self.sent_agent = SentimentAgent()
        self.metrics_agent = MetricsAgent()
        self.vol_agent = VolatilityAgent()

        self.synthesis_agent = RiskSynthesisAgent()
        self.audit_logger = AuditLogger(source_filename=source_filename)

    async def analyze(self, result_json: dict):
        """
        Orchestrates the full 6-Layer Risk Analysis pipeline.
        - Layer 0: Signal Validation
        - Layer 1: Context Aggregation
        - Layer 2: Fast Rule Engine
        - Layer 3: Specialized Sub-Agents
        - Layer 4: LLM Orchestration
        - Layer 5: Decision Gate
        - Layer 6: Structured Output & Audit Logging
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
            source = context.market_data.get('source') if context.market_data else 'no_source'
            print(f"Context aggregated from {source}")

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
        print(f"Fast rules passed. R:R: {metrics['rr_ratio']}")

        # Layer 3: Specialized Sub-Agents
        print(f"\n--- Layer 3: Executing Specialized Agents ---")
        agent_tasks = [
            asyncio.to_thread(self.tech_agent.analyze, signal, context),
            asyncio.to_thread(self.sent_agent.analyze, signal, context),
            asyncio.to_thread(self.metrics_agent.analyze, signal, context),
            asyncio.to_thread(self.vol_agent.analyze, signal, context)
        ]
        
        agent_results = await asyncio.gather(*agent_tasks)
        
        reports = {
            "technical": agent_results[0],
            "sentiment": agent_results[1],
            "metrics": agent_results[2],
            "volatility": agent_results[3]
        }
        
        for name, report in reports.items():
            reasoning = report.get('reasoning', report.get('reason', 'No reasoning provided'))
            print(f"Agent {name.capitalize()}: Score {report['score']} - {reasoning[:50]}...")

        # Layer 4: LLM Orchestration
        print(f"\n--- Layer 4: LLM Synthesis ---")
        synthesis_report = await self.synthesis_agent.synthesize(signal, reports)
        composite_score = synthesis_report.get("composite_score", 50)
        print(f"Composite Score: {composite_score} - Rationale: {synthesis_report.get('rationale', '')[:100]}...")

        # Layer 5: Decision Gate (Final Override)
        print(f"\n--- Layer 5: Decision Gate ---")
        final_decision = self.decision_gate.make_final_decision(composite_score, metrics)
        
        # Layer 6: Structured Output & Audit Logging
        print(f"--- Layer 6: Finalizing Audit ---")
        
        report = RiskAnalysisReport(
            signal=signal,
            context=context,
            metrics=metrics,
            agent_reports=reports,
            synthesis=synthesis_report,
            decision=final_decision["decision"],
            composite_score=composite_score,
            rationale=final_decision["rationale"],
            suggested_adjustments=synthesis_report.get("suggested_adjustments")
        )

        # Persist decision
        await self.audit_logger.log_decision(report)
        
        return report.model_dump()

async def run_example(result_json):
    analyzer = RiskAnalyzer()
    analysis_result = await analyzer.analyze(result_json)
    print("\n--- Final Output ---")
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
