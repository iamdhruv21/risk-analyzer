import os
import json
from typing import Dict, Any
from anthropic import AsyncAnthropic
from src.models.signal import TradeSignal, RiskContext

class RiskSynthesisAgent:
    """Layer 4: Risk Synthesis Engine (LLM Orchestration)"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"

    async def synthesize(self, signal: TradeSignal, agent_reports: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregates sub-agent outputs into a unified assessment using Claude.
        """
        required_agents = ["technical", "metrics", "volatility", "sentiment"]
        missing_agents = [agent for agent in required_agents if agent not in agent_reports]

        if missing_agents:
            return {
                "composite_score": None,
                "rationale": f"Cannot calculate composite score: Missing reports from {', '.join(missing_agents)}",
                "warnings": [f"Missing agent reports: {', '.join(missing_agents)}"]
            }

        invalid_scores = []
        for agent, report in agent_reports.items():
            score = report.get("score")
            if score is None or not isinstance(score, (int, float)) or score < 0 or score > 100:
                invalid_scores.append(agent)

        if invalid_scores:
            return {
                "composite_score": None,
                "rationale": f"Cannot calculate composite score: Invalid or missing scores from {', '.join(invalid_scores)}. Insufficient data for risk assessment.",
                "warnings": [f"Invalid/missing scores from: {', '.join(invalid_scores)}"]
            }

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_anthropic_key_here":
            weights = {"technical": 0.3, "metrics": 0.3, "volatility": 0.25, "sentiment": 0.15}
            score = sum(agent_reports[k]["score"] * weights[k] for k in weights if k in agent_reports)
            return {
                "composite_score": round(score, 2),
                "rationale": "Fallback: Weighted average used (Anthropic API key missing).",
                "warnings": ["LLM Synthesis skipped - API key not configured."]
            }

        system_prompt = """
        You are a Senior Risk Manager at a top-tier hedge fund. 
        Your task is to synthesize four specialized risk reports into a single, unified trade decision.
        
        Input:
        1. Trade Signal (Asset, Type, Price, TP, SL, Leverage)
        2. Technical Analysis Report (Score + Indicators)
        3. Sentiment & News Report (Score + News Context)
        4. Trade Metrics Report (R:R, Liquidation Risk)
        5. Volatility & Regime Report (Market Environment)
        
        Guidelines:
        - Weighting (Internal Guide): Technical (30%), Metrics (30%), Volatility (25%), Sentiment (15%).
        - Look for contradictions (e.g., strong technical score but high-impact news event).
        - Be conservative. If liquidation risk is high or volatility regime is unstable, lower the score.
        - Output MUST be a structured JSON object.
        """

        user_content = f"""
        Analyze this trade and provide a unified risk assessment.
        
        SIGNAL: {signal.model_dump_json()}
        REPORTS: {json.dumps(agent_reports)}
        
        Required JSON Output Format:
        {{
            "composite_score": 0-100,
            "rationale": "Short professional explanation",
            "warnings": ["Warning 1", "Warning 2"],
            "suggested_adjustments": {{
                "leverage": "New leverage or same",
                "position_size_multiplier": 0.0-1.0
            }}
        }}
        """

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            # Basic JSON extraction in case Claude adds markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Error in LLM Synthesis: {e}")
            return {
                "composite_score": 50,
                "rationale": f"LLM synthesis failed: {str(e)}",
                "warnings": ["Synthesis Error"]
            }
