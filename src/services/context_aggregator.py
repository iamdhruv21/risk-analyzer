import os
import asyncio
import aiohttp
import ccxt.async_support as ccxt
from typing import Dict, Any
from dotenv import load_dotenv
from src.models.signal import TradeSignal, RiskContext

# Load environment variables from .env
load_dotenv()

class ContextAggregator:
    def __init__(self):
        self.session = None
        self.binance_key = os.getenv("BINANCE_API_KEY")
        self.binance_secret = os.getenv("BINANCE_API_SECRET")
        self.exchange = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        # Initialize CCXT Binance
        self.exchange = ccxt.binance({
            'apiKey': self.binance_key,
            'secret': self.binance_secret,
            'enableRateLimit': True,
        })
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.exchange:
            await self.exchange.close()

    async def fetch_market_data(self, asset: str) -> Dict[str, Any]:
        """Fetch live market data from Binance if keys are provided, otherwise fallback to mock."""
        if self.exchange and self.binance_key != "your_api_key_here":
            try:
                symbol = f"{asset}/USDT"
                ticker = await self.exchange.fetch_ticker(symbol)
                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=20)
                
                return {
                    "current_price": ticker['last'],
                    "high_24h": ticker['high'],
                    "low_24h": ticker['low'],
                    "volume_24h": ticker['baseVolume'],
                    "ohlcv": ohlcv,
                    "source": "live_binance"
                }
            except Exception as e:
                print(f"Error fetching live Binance data: {e}")
                # Fallback to mock logic below

        # Mocking async fetch (Fallback)
        await asyncio.sleep(0.1)
        return {
            "current_price": 65200.0,
            "atr_14": 1200.5,
            "volume_24h": 500000000,
            "ohlcv": [],
            "source": "mock"
        }

    async def fetch_news_data(self, asset: str) -> list:
        """Fetch live headlines and sentiment from Alpha Vantage."""
        av_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        
        if av_key and av_key != "your_alpha_vantage_key_here":
            try:
                # Alpha Vantage News & Sentiment endpoint
                # We filter by tickers (e.g., CRYPTO:BTC or just BTC)
                ticker = f"CRYPTO:{asset}" if asset in ["BTC", "ETH"] else asset
                url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={av_key}"
                
                async with self.session.get(url) as response:
                    data = await response.json()
                    feed = data.get("feed", [])
                    
                    results = []
                    for item in feed[:5]: # Take top 5 latest news
                        # Map Alpha Vantage sentiment labels to scores if needed, 
                        # but they already provide a 'ticker_sentiment_score'
                        ticker_sentiment = 0.5
                        for t in item.get("ticker_sentiment", []):
                            if t.get("ticker") == asset:
                                ticker_sentiment = float(t.get("ticker_sentiment_score", 0.5))
                                break
                        
                        results.append({
                            "headline": item.get("title"),
                            "sentiment": (ticker_sentiment + 1) / 2, # Normalize -1 to 1 into 0 to 1
                            "url": item.get("url"),
                            "source": item.get("source")
                        })
                    
                    if results:
                        return results
            except Exception as e:
                print(f"Error fetching Alpha Vantage news: {e}")

        # Fallback to mock
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
        """Fetch live account balance from Binance if keys are provided."""
        if self.exchange and self.binance_key != "your_api_key_here":
            try:
                balance = await self.exchange.fetch_balance()
                # Simplified: Get USDT equity
                usdt_balance = balance.get('USDT', {})
                return {
                    "equity": usdt_balance.get('total', 0.0),
                    "free": usdt_balance.get('free', 0.0),
                    "source": "live_binance"
                }
            except Exception as e:
                print(f"Error fetching Binance balance: {e}")

        await asyncio.sleep(0.05)
        return {
            "equity": 10000.0,
            "balance": 9500.0,
            "open_positions": [],
            "daily_drawdown": 0.02,
            "source": "mock"
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
