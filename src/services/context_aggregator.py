import os
import asyncio
import aiohttp
import ccxt.async_support as ccxt
from typing import Dict, Any
from dotenv import load_dotenv
from src.models.signal import TradeSignal, RiskContext
from src.services.indian_market_data import IndianMarketDataProvider
from src.services.news_aggregator import NewsAggregator

# Load environment variables from .env
load_dotenv()

class ContextAggregator:
    def __init__(self):
        self.session = None
        self.binance_key = os.getenv("BINANCE_API_KEY")
        self.binance_secret = os.getenv("BINANCE_API_SECRET")
        self.exchange = None
        self.indian_market = None
        self.news_aggregator = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        # Initialize CCXT Binance
        self.exchange = ccxt.binance({
            'apiKey': self.binance_key,
            'secret': self.binance_secret,
            'enableRateLimit': True,
        })
        # Initialize Indian market data provider
        self.indian_market = IndianMarketDataProvider(self.session)
        # Initialize news aggregator
        self.news_aggregator = NewsAggregator(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.exchange:
            await self.exchange.close()

    def _get_yfinance_symbol(self, asset: str, asset_class: str) -> str:
        """Map asset to Yahoo Finance symbol"""
        # Indian Indices
        if asset.upper() == "NIFTY":
            return "^NSEI"
        elif asset.upper() == "SENSEX":
            return "^BSESN"
        elif asset.upper() == "BANKNIFTY":
            return "^NSEBANK"

        # Commodities
        elif asset.upper() == "GOLD":
            return "GC=F"  # Gold Futures
        elif asset.upper() == "SILVER":
            return "SI=F"  # Silver Futures
        elif asset.upper() == "CRUDE" or asset.upper() == "OIL":
            return "CL=F"  # Crude Oil Futures

        # Indian Stocks - append .NS for NSE or .BO for BSE
        elif asset_class == "stock":
            # If asset already has exchange suffix, use as is
            if asset.endswith('.NS') or asset.endswith('.BO'):
                return asset
            # Default to NSE
            return f"{asset}.NS"

        # Default: return as is for other assets
        return asset

    async def fetch_market_data_yfinance(self, asset: str, asset_class: str) -> Dict[str, Any] | None:
        """Fetch market data from Yahoo Finance (for Indian stocks, indices, commodities)"""
        try:
            import yfinance as yf
            import pandas_ta as ta

            symbol = self._get_yfinance_symbol(asset, asset_class)
            ticker = yf.Ticker(symbol)

            # Get current data
            info = ticker.info
            hist = ticker.history(period="1mo", interval="1h")

            if hist.empty:
                print(f"No historical data available for {asset} ({symbol})")
                return None

            current_price = hist['Close'].iloc[-1]

            # Calculate ATR (14-period)
            hist_with_atr = hist.copy()
            hist_with_atr.ta.atr(length=14, append=True)
            atr_14 = hist_with_atr[f'ATRr_14'].iloc[-1] if f'ATRr_14' in hist_with_atr.columns else 0

            # Convert DataFrame to list for OHLCV - add timestamp as first column
            # Format: [timestamp, open, high, low, close, volume]
            ohlcv = []
            for idx, row in hist.iterrows():
                ohlcv.append([
                    int(idx.timestamp() * 1000),  # timestamp in milliseconds
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    float(row['Volume'])
                ])

            return {
                "current_price": float(current_price),
                "high_24h": float(hist['High'].tail(24).max()) if len(hist) >= 24 else float(hist['High'].max()),
                "low_24h": float(hist['Low'].tail(24).min()) if len(hist) >= 24 else float(hist['Low'].min()),
                "volume_24h": float(hist['Volume'].tail(24).sum()) if len(hist) >= 24 else float(hist['Volume'].sum()),
                "atr_14": float(atr_14) if atr_14 else 0,
                "ohlcv": ohlcv,
                "source": "yfinance",
                "symbol": symbol
            }
        except Exception as e:
            print(f"Error fetching Yahoo Finance data for {asset}: {e}")
            return None

    async def fetch_market_data(self, asset: str, asset_class: str = "crypto") -> Dict[str, Any] | None:
        """
        Fetch live market data from appropriate source based on asset class.

        Crypto: Binance
        Stocks/Indices/Commodities: Yahoo Finance
        """
        # For crypto, try Binance first
        if asset_class == "crypto":
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

        # For stocks, indices, and commodities, use Yahoo Finance
        else:
            return await self.fetch_market_data_yfinance(asset, asset_class)

    async def fetch_news_data(self, asset: str, asset_class: str = "crypto") -> list | None:
        """
        Fetch news using the multi-source news aggregator
        Supports: Indian stocks, crypto, commodities, US stocks
        """
        if not self.news_aggregator:
            print("News aggregator not initialized")
            return None

        return await self.news_aggregator.fetch_news(asset, asset_class)

    async def fetch_economic_calendar(self) -> list | None:
        """Fetch scheduled high-impact events. Returns None as no API integration is configured."""
        print("Economic calendar API not configured. Returning None.")
        return None

    async def fetch_portfolio_state(self) -> Dict[str, Any] | None:
        """
        Fetch live account balance.

        For crypto: Binance
        For stocks: Can integrate with Groww API or other broker APIs

        Note: You need to configure portfolio equity in .env if not using live broker APIs
        """
        # Try Binance for crypto portfolio
        if self.exchange and self.binance_key and self.binance_key != "your_api_key_here":
            try:
                balance = await self.exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {})

                return {
                    "equity": usdt_balance.get('total', 0.0),
                    "free": usdt_balance.get('free', 0.0),
                    "source": "live_binance",
                    "daily_drawdown": 0.0  # You need to track this separately
                }
            except Exception as e:
                print(f"Error fetching Binance balance: {e}")

        # Fallback: Use configured portfolio value from .env
        portfolio_equity = os.getenv("PORTFOLIO_EQUITY")
        if portfolio_equity:
            try:
                equity_value = float(portfolio_equity)
                print(f"Using configured portfolio equity: {equity_value}")
                return {
                    "equity": equity_value,
                    "free": equity_value,
                    "source": "configured",
                    "daily_drawdown": 0.0
                }
            except ValueError:
                print(f"Invalid PORTFOLIO_EQUITY value in .env: {portfolio_equity}")

        print("Portfolio state unavailable. Configure PORTFOLIO_EQUITY in .env or setup broker API.")
        return None

    async def fetch_sentiment_data(self, asset_class: str = "crypto") -> Dict[str, Any] | None:
        """
        Fetch sentiment data based on market type

        For Crypto: Fear & Greed Index
        For US Stocks: VIX
        For Indian Stocks: India VIX + MMI

        All APIs are FREE - no keys required
        """
        sentiment_data = {}

        # For crypto assets - fetch Fear & Greed Index
        if asset_class == "crypto":
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
                            print(f"✓ Crypto Fear & Greed: {fng.get('value')} ({fng.get('value_classification')})")
            except Exception as e:
                print(f"Error fetching Fear & Greed Index: {e}")

        # For Indian stocks/indices - fetch India VIX and MMI
        if asset_class == "stock" or asset_class == "index":
            if self.indian_market:
                # Fetch India VIX
                india_vix = await self.indian_market.fetch_india_vix()
                if india_vix:
                    sentiment_data["india_vix"] = {
                        "value": india_vix,
                        "interpretation": self._interpret_vix(india_vix)
                    }

                # Fetch MMI (Market Momentum Index)
                mmi = await self.indian_market.calculate_mmi()
                if mmi:
                    sentiment_data["mmi"] = {
                        "value": mmi,
                        "interpretation": self.indian_market._interpret_mmi(mmi)
                    }

        # For US stocks - fetch VIX
        if asset_class in ["stock", "index"] and not sentiment_data.get("india_vix"):
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
                    print(f"✓ US VIX: {current_vix:.2f}")
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
            self.fetch_market_data(signal.asset, signal.assetClass),
            self.fetch_news_data(signal.asset, signal.assetClass),
            self.fetch_economic_calendar(),
            self.fetch_portfolio_state(),
            self.fetch_sentiment_data(signal.assetClass)
        ]

        results = await asyncio.gather(*tasks)

        return RiskContext(
            market_data=results[0],
            news_data=results[1],
            economic_calendar=results[2],
            portfolio_state=results[3],
            sentiment=results[4]
        )
