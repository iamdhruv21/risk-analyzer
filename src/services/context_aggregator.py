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

    async def fetch_market_data(self, asset: str) -> Dict[str, Any] | None:
        """Fetch live market data from Binance. Returns None if API keys are not configured or request fails."""
        if not self.exchange or not self.binance_key or self.binance_key == "your_api_key_here":
            print(f"Binance API keys not configured. Cannot fetch market data for {asset}")
            return None

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
            print(f"Error fetching live Binance data for {asset}: {e}")
            return None

    async def fetch_news_data(self, asset: str) -> list | None:
        """Fetch live headlines and sentiment from Alpha Vantage. Returns None if API key is not configured or request fails."""
        av_key = os.getenv("ALPHA_VANTAGE_API_KEY")

        if not av_key or av_key == "your_alpha_vantage_key_here":
            print(f"Alpha Vantage API key not configured. Cannot fetch news data for {asset}")
            return None

        try:
            ticker = f"CRYPTO:{asset}" if asset in ["BTC", "ETH"] else asset
            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={av_key}"

            async with self.session.get(url) as response:
                data = await response.json()
                feed = data.get("feed", [])

                if not feed:
                    print(f"No news data available for {asset}")
                    return None

                results = []
                for item in feed[:5]:
                    ticker_sentiment = 0.5
                    for t in item.get("ticker_sentiment", []):
                        if t.get("ticker") == asset:
                            ticker_sentiment = float(t.get("ticker_sentiment_score", 0.5))
                            break

                    results.append({
                        "headline": item.get("title"),
                        "sentiment": (ticker_sentiment + 1) / 2,
                        "url": item.get("url"),
                        "source": item.get("source")
                    })

                return results if results else None
        except Exception as e:
            print(f"Error fetching Alpha Vantage news for {asset}: {e}")
            return None

    async def fetch_economic_calendar(self) -> list | None:
        """Fetch scheduled high-impact events. Returns None as no API integration is configured."""
        print("Economic calendar API not configured. Returning None.")
        return None

    async def fetch_portfolio_state(self) -> Dict[str, Any] | None:
        """Fetch live account balance from Binance. Returns None if API keys are not configured or request fails."""
        if not self.exchange or not self.binance_key or self.binance_key == "your_api_key_here":
            print("Binance API keys not configured. Cannot fetch portfolio state.")
            return None

        try:
            balance = await self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {})

            return {
                "equity": usdt_balance.get('total', 0.0),
                "free": usdt_balance.get('free', 0.0),
                "source": "live_binance"
            }
        except Exception as e:
            print(f"Error fetching Binance balance: {e}")
            return None

    async def fetch_sentiment_data(self) -> Dict[str, Any] | None:
        """
        Fetch Fear/Greed index and VIX from free APIs.

        APIs used (no keys required):
        - Fear & Greed Index: https://api.alternative.me/fng/ (FREE)
        - VIX: Yahoo Finance via yfinance library (FREE)

        Returns None if all API calls fail.
        """
        sentiment_data = {}

        # Fetch Fear & Greed Index (Crypto market sentiment)
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("data"):
                        fng = data["data"][0]
                        sentiment_data["fear_greed_index"] = {
                            "value": int(fng.get("value", 50)),
                            "classification": fng.get("value_classification", "Neutral"),
                            "timestamp": fng.get("timestamp")
                        }
        except Exception as e:
            print(f"Error fetching Fear & Greed Index: {e}")

        # Fetch VIX (Volatility Index - market fear gauge)
        try:
            import yfinance as yf
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="1d")

            if not vix_hist.empty:
                current_vix = vix_hist['Close'].iloc[-1]
                sentiment_data["vix"] = {
                    "value": round(float(current_vix), 2),
                    "interpretation": self._interpret_vix(current_vix)
                }
        except Exception as e:
            print(f"Error fetching VIX: {e}")

        return sentiment_data if sentiment_data else None

    def _interpret_vix(self, vix_value: float) -> str:
        """Interpret VIX value into risk level"""
        if vix_value < 12:
            return "Very Low Volatility"
        elif vix_value < 20:
            return "Low Volatility"
        elif vix_value < 30:
            return "Moderate Volatility"
        elif vix_value < 40:
            return "High Volatility"
        else:
            return "Extreme Volatility"

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
