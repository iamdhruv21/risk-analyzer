from typing import Dict, Any
from src.models.signal import TradeSignal, RiskContext

class SentimentAgent:
    """Agent B: The Macro Desk"""
    
    def analyze(self, signal: TradeSignal, context: RiskContext) -> Dict[str, Any]:
        news = context.news_data
        calendar = context.economic_calendar
        
        if not news:
            return {"score": 50, "reason": "No news data available"}

        # Simplified sentiment aggregation
        total_sentiment = sum(item.get("sentiment", 0.5) for item in news)
        avg_sentiment = total_sentiment / len(news)
        
        score = 50 + (avg_sentiment - 0.5) * 100
        reasons = [f"Average news sentiment: {avg_sentiment:.2f}"]

        # Check for high-impact events
        high_impact = [e for e in calendar if e.get("impact") == "HIGH"]
        if high_impact:
            score -= 20
            reasons.append(f"High impact events detected: {[e['event'] for e in high_impact]}")

        return {
            "score": max(0, min(100, score)),
            "reasoning": "; ".join(reasons),
            "avg_sentiment": round(avg_sentiment, 2)
        }
