"""
Multi-Source News Aggregator
Aggregates news from multiple sources for different markets
"""

import os
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class NewsAggregator:
    """Aggregate news from multiple sources based on asset and market"""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    async def fetch_news(self, asset: str, asset_class: str = "crypto") -> Optional[List[Dict[str, Any]]]:
        """
        Fetch news from the best available source for the asset

        Priority:
        1. NewsAPI (multi-market, best coverage)
        2. Alpha Vantage (fallback for stocks)
        """

        # Try NewsAPI first (if configured)
        if self.news_api_key and self.news_api_key != "your_news_api_key_here":
            news = await self._fetch_from_newsapi(asset, asset_class)
            if news:
                return news

        # Fallback to Alpha Vantage
        if self.alpha_vantage_key and self.alpha_vantage_key != "your_alpha_vantage_key_here":
            news = await self._fetch_from_alpha_vantage(asset, asset_class)
            if news:
                return news

        print(f"⚠ No news API configured. Configure NEWS_API_KEY in .env")
        return None

    async def _fetch_from_newsapi(self, asset: str, asset_class: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch news from NewsAPI
        FREE tier: 100 requests/day
        Coverage: Global news including Indian markets, crypto, commodities
        """
        try:
            # Build search query based on asset and class
            query = self._build_newsapi_query(asset, asset_class)

            # Get news from last 7 days
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 5,
                "apiKey": self.news_api_key
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get("articles", [])

                    if not articles:
                        print(f"⚠ No news found for {asset} from NewsAPI")
                        return None

                    results = []
                    for article in articles:
                        results.append({
                            "headline": article.get("title"),
                            "description": article.get("description"),
                            "sentiment": 0.5,  # NewsAPI doesn't provide sentiment
                            "url": article.get("url"),
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "published_at": article.get("publishedAt")
                        })

                    print(f"✓ Fetched {len(results)} news articles from NewsAPI for {asset}")
                    return results
                elif response.status == 429:
                    print(f"⚠ NewsAPI rate limit exceeded (100 requests/day)")
                    return None
                elif response.status == 401:
                    print(f"⚠ Invalid NewsAPI key. Get one from https://newsapi.org/register")
                    return None
                else:
                    print(f"⚠ NewsAPI returned status {response.status}")
                    return None

        except Exception as e:
            print(f"Error fetching news from NewsAPI: {e}")
            return None

    async def _fetch_from_alpha_vantage(self, asset: str, asset_class: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch news from Alpha Vantage (fallback)
        Provides sentiment scores
        """
        try:
            # Alpha Vantage ticker format
            if asset_class == "crypto":
                ticker = f"CRYPTO:{asset}"
            else:
                ticker = asset

            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={self.alpha_vantage_key}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Check for API limit message
                    if "Note" in data or "Information" in data:
                        print(f"⚠ Alpha Vantage API limit reached")
                        return None

                    feed = data.get("feed", [])

                    if not feed:
                        print(f"⚠ No news found for {asset} from Alpha Vantage")
                        return None

                    results = []
                    for item in feed[:5]:
                        # Extract ticker-specific sentiment
                        ticker_sentiment = 0.5
                        for t in item.get("ticker_sentiment", []):
                            if asset in t.get("ticker", ""):
                                ticker_sentiment = float(t.get("ticker_sentiment_score", 0.5))
                                # Normalize from [-1, 1] to [0, 1]
                                ticker_sentiment = (ticker_sentiment + 1) / 2
                                break

                        results.append({
                            "headline": item.get("title"),
                            "sentiment": ticker_sentiment,
                            "url": item.get("url"),
                            "source": item.get("source", "Alpha Vantage"),
                            "published_at": item.get("time_published")
                        })

                    print(f"✓ Fetched {len(results)} news articles from Alpha Vantage for {asset}")
                    return results
                else:
                    print(f"⚠ Alpha Vantage returned status {response.status}")
                    return None

        except Exception as e:
            print(f"Error fetching news from Alpha Vantage: {e}")
            return None

    def _build_newsapi_query(self, asset: str, asset_class: str) -> str:
        """Build search query for NewsAPI based on asset and class"""

        # For Indian stocks/indices
        if asset.upper() in ["NIFTY", "SENSEX", "BANKNIFTY"]:
            return f"{asset} India stock market"

        # For Indian companies
        if asset.endswith('.NS') or asset.endswith('.BO'):
            company_name = asset.split('.')[0]
            return f"{company_name} India stock"

        # For crypto
        if asset_class == "crypto":
            if asset.upper() == "BTC":
                return "Bitcoin cryptocurrency"
            elif asset.upper() == "ETH":
                return "Ethereum cryptocurrency"
            else:
                return f"{asset} cryptocurrency"

        # For commodities
        if asset.upper() in ["GOLD", "SILVER", "CRUDE", "OIL"]:
            return f"{asset} commodity market"

        # Default: use asset name
        return asset
