import os
import json
from typing import Dict, Any
from anthropic import AsyncAnthropic
from groq import AsyncGroq
from src.models.signal import TradeSignal, RiskContext

class RiskSynthesisAgent:
    """Layer 4: Risk Synthesis Engine (LLM Orchestration)"""

    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")

        if self.anthropic_key and self.anthropic_key != "your_anthropic_key_here":
            self.client = AsyncAnthropic(api_key=self.anthropic_key)
            self.model = "claude-3-5-sonnet-20241022"
            self.provider = "anthropic"
        elif self.groq_key:
            self.client = AsyncGroq(api_key=self.groq_key)
            self.model = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
            self.provider = "groq"
        else:
            self.client = None
            self.provider = "fallback"

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

        # Fallback to weighted average if no LLM provider available
        if self.provider == "fallback":
            weights = {"technical": 0.3, "metrics": 0.3, "volatility": 0.25, "sentiment": 0.15}
            score = sum(agent_reports[k]["score"] * weights[k] for k in weights if k in agent_reports)
            return {
                "composite_score": round(score, 2),
                "rationale": "Fallback: Weighted average used (No API keys configured).",
                "warnings": ["LLM Synthesis skipped - No API keys configured."]
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
            if self.provider == "anthropic":
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_content}]
                )
                content = response.content[0].text
            elif self.provider == "groq":
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=1000,
                    temperature=0
                )
                content = response.choices[0].message.content

            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()

            result = json.loads(content)
            result["synthesis_provider"] = self.provider
            return result

        except Exception as e:
            print(f"Error in LLM Synthesis ({self.provider}): {e}")
            return {
                "composite_score": 50,
                "rationale": f"LLM synthesis failed ({self.provider}): {str(e)}",
                "warnings": ["Synthesis Error"],
                "synthesis_provider": f"{self.provider}_error"
            }
