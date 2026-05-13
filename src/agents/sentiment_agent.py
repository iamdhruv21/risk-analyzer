from typing import Dict, Any
from src.models.signal import TradeSignal, RiskContext

class SentimentAgent:
    """Agent B: The Macro Desk"""

    def analyze(self, signal: TradeSignal, context: RiskContext) -> Dict[str, Any]:
        if context.sentiment is None and context.news_data is None:
            return {
                "score": None,
                "reasoning": "Sentiment and news data unavailable - cannot perform sentiment analysis",
                "avg_sentiment": None,
                "mmi": None,
                "fear_greed_index": None
            }

        news = context.news_data
        calendar = context.economic_calendar
        sentiment_data = context.sentiment

        score = 50
        reasons = []

        # 1. News Sentiment Analysis with Inverse Correlation Detection
        if news and len(news) > 0:
            total_sentiment = sum(item.get("sentiment", 0.5) for item in news)
            avg_sentiment = total_sentiment / len(news)

            # Check for inverse correlation scenario (bad news = good market)
            # Example: Central bank rate cuts (often negative news) can boost markets
            inverse_keywords = ["rate cut", "stimulus", "easing", "bailout", "intervention", "support"]
            bullish_on_bad_news = False

            for item in news:
                headline = item.get("headline", "").lower()
                item_sentiment = item.get("sentiment", 0.5)

                # If headline contains inverse keywords and sentiment is low, it might be bullish
                if any(keyword in headline for keyword in inverse_keywords) and item_sentiment < 0.4:
                    bullish_on_bad_news = True
                    break

            if bullish_on_bad_news:
                # Inverse scenario detected: bad news is actually positive for market
                news_score = 60 + (1 - avg_sentiment) * 30  # Invert the sentiment
                reasons.append(f"Inverse correlation detected: Negative news ({avg_sentiment:.2f}) is bullish (policy support)")
            else:
                # Normal correlation: good news = good market
                news_score = 50 + (avg_sentiment - 0.5) * 100
                reasons.append(f"News sentiment: {avg_sentiment:.2f}")

            score = news_score
        else:
            reasons.append("No news data available")

        # 2. MMI (Market Movement Insight) - Higher MMI suggests stronger momentum
        mmi_data = sentiment_data.get("mmi") if sentiment_data else None
        mmi = mmi_data.get("value") if isinstance(mmi_data, dict) else mmi_data
        if mmi is not None:
            if mmi > 70:
                score += 10
                reasons.append(f"Strong MMI momentum: {mmi}")
            elif mmi < 30:
                score -= 10
                reasons.append(f"Weak MMI momentum: {mmi}")
            else:
                reasons.append(f"Neutral MMI: {mmi}")

        # 3. Fear & Greed Index - Higher greed can be a contrarian signal
        fear_greed_data = sentiment_data.get("fear_greed_index") if sentiment_data else None
        fear_greed = None
        if fear_greed_data is not None:
            # Extract numeric value if it's a dict (new format)
            fear_greed = fear_greed_data.get("value") if isinstance(fear_greed_data, dict) else fear_greed_data

        if fear_greed is not None:
            classification = fear_greed_data.get("classification", "") if isinstance(fear_greed_data, dict) else ""

            if fear_greed > 75:
                # Extreme greed - contrarian bearish signal
                score -= 15
                reasons.append(f"Extreme greed detected ({fear_greed}, {classification}) - contrarian caution")
            elif fear_greed < 25:
                # Extreme fear - contrarian bullish signal
                score += 15
                reasons.append(f"Extreme fear detected ({fear_greed}, {classification}) - contrarian opportunity")
            elif 40 <= fear_greed <= 60:
                score += 5
                reasons.append(f"Neutral sentiment ({fear_greed}, {classification}) - balanced market")
            else:
                reasons.append(f"Fear & Greed Index: {fear_greed} ({classification})")

        # 4. Market Regime Consideration
        regime = sentiment_data.get("market_regime") if sentiment_data else None
        if regime and regime == "bullish_expansion" and signal.type == "BUY":
            score += 10
            reasons.append("Regime aligned with BUY signal")
        elif regime == "bearish_capitulation" and signal.type == "SELL":
            score += 10
            reasons.append("Regime aligned with SELL signal")
        elif regime == "bullish_expansion" and signal.type == "SELL":
            score -= 10
            reasons.append("SELL signal against bullish regime")
        elif regime == "bearish_capitulation" and signal.type == "BUY":
            score -= 10
            reasons.append("BUY signal against bearish regime")

        # 5. Check for high-impact events
        high_impact = [e for e in calendar if e.get("impact") == "HIGH"] if calendar else []
        if high_impact:
            score -= 20
            reasons.append(f"High impact events detected: {[e['event'] for e in high_impact]}")

        return {
            "score": max(0, min(100, score)),
            "reasoning": "; ".join(reasons),
            "avg_sentiment": round(sum(item.get("sentiment", 0.5) for item in news) / len(news), 2) if news else None,
            "mmi": mmi,
            "fear_greed_index": fear_greed,
            "fear_greed_classification": fear_greed_data.get("classification") if isinstance(fear_greed_data, dict) else None
        }
