import asyncio
import aiohttp
from typing import Dict, Any
from src.models.signal import TradeSignal, RiskContext

class ContextAggregator:
    def __init__(self):
        # In a real scenario, API keys would be loaded here from env
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_market_data(self, asset: str) -> Dict[str, Any]:
        """Fetch real-time price, candles, and order book depth"""
        # Mocking async fetch
        await asyncio.sleep(0.1)
        return {
            "current_price": 65200.0,
            "atr_14": 1200.5,
            "volume_24h": 500000000,
            "ohlcv": [] # last 200 candles would be here
        }

    async def fetch_news_data(self, asset: str) -> list:
        """Fetch last 24h headlines for the asset"""
        await asyncio.sleep(0.2)
        return [
            {"headline": "BTC ETFs see record inflows", "sentiment": 0.8},
            {"headline": "Central bank hints at rate cut", "sentiment": 0.5}
        ]

    async def fetch_economic_calendar(self) -> list:
        """Fetch scheduled high-impact events"""
        await asyncio.sleep(0.15)
        return [
            {"event": "FOMC Meeting", "time": "2026-05-01T18:00:00Z", "impact": "HIGH"}
        ]

    async def fetch_portfolio_state(self) -> Dict[str, Any]:
        """Fetch current positions and account equity"""
        await asyncio.sleep(0.05)
        return {
            "equity": 10000.0,
            "balance": 9500.0,
            "open_positions": [],
            "daily_drawdown": 0.02
        }

    async def fetch_sentiment_data(self) -> Dict[str, Any]:
        """Fetch Fear/Greed index, VIX, etc."""
        await asyncio.sleep(0.1)
        return {
            "fear_greed_index": 65,
            "market_regime": "bullish_expansion"
        }

    async def aggregate_all_context(self, signal: TradeSignal) -> RiskContext:
        """Parallel Data Fetch using asyncio.gather"""
        tasks = [
            self.fetch_market_data(signal.asset),
            self.fetch_news_data(signal.asset),
            self.fetch_economic_calendar(),
            self.fetch_portfolio_state(),
            self.fetch_sentiment_data()
        ]
        
        results = await asyncio.gather(*tasks)
        
        return RiskContext(
            market_data=results[0],
            news_data=results[1],
            economic_calendar=results[2],
            portfolio_state=results[3],
            sentiment=results[4]
        )
