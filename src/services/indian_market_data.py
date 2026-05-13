"""
Indian Market Data Provider
Fetches India-specific data from NSE APIs (all free, no API keys required)
"""

import aiohttp
from typing import Dict, Any, Optional


class IndianMarketDataProvider:
    """Fetch Indian market-specific data from NSE"""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.nse_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/'
        }

    async def fetch_india_vix(self) -> Optional[float]:
        try:
            url = "https://www.nseindia.com/api/allIndices"
            async with self.session.get(url, headers=self.nse_headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Find India VIX in the indices list
                    for index in data.get('data', []):
                        if index.get('index') == 'INDIA VIX':
                            vix_value = float(index.get('last', 0))
                            print(f"✓ India VIX: {vix_value}")
                            return vix_value

                    print("India VIX not found in NSE response")
                    return None
                else:
                    print(f"NSE API returned status {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching India VIX: {e}")
            return None

    async def fetch_market_breadth(self) -> Optional[Dict[str, Any]]:
        try:
            url = "https://www.nseindia.com/api/market-data-pre-open?key=ALL"
            async with self.session.get(url, headers=self.nse_headers) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract advance/decline data
                    advances = 0
                    declines = 0
                    unchanged = 0

                    for stock in data.get('data', []):
                        change = float(stock.get('pChange', 0))
                        if change > 0:
                            advances += 1
                        elif change < 0:
                            declines += 1
                        else:
                            unchanged += 1

                    total = advances + declines + unchanged

                    if total > 0:
                        breadth = {
                            "advances": advances,
                            "declines": declines,
                            "unchanged": unchanged,
                            "total": total,
                            "advance_decline_ratio": advances / declines if declines > 0 else 0,
                            "advance_percentage": (advances / total) * 100
                        }
                        print(f"✓ Market Breadth: {advances} advances, {declines} declines")
                        return breadth

                    return None
                else:
                    print(f"NSE market breadth API returned status {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching market breadth: {e}")
            return None

    async def calculate_mmi(self) -> Optional[float]:
        """
        Calculate Market Momentum Index (MMI) for Indian markets
        Based on market breadth data

        MMI Scale: 0-100
        - 0-30: Oversold (bullish signal)
        - 30-70: Neutral
        - 70-100: Overbought (bearish signal)
        """
        breadth = await self.fetch_market_breadth()

        if not breadth:
            return None

        try:
            # Simple MMI calculation based on advance/decline ratio
            # This is a simplified version - can be enhanced with more metrics

            advance_pct = breadth['advance_percentage']

            # Normalize to 0-100 scale
            # If 100% advances -> MMI = 100 (overbought)
            # If 0% advances (100% declines) -> MMI = 0 (oversold)
            mmi = advance_pct

            print(f"✓ MMI calculated: {mmi:.2f}")
            return round(mmi, 2)
        except Exception as e:
            print(f"Error calculating MMI: {e}")
            return None

    def _interpret_mmi(self, mmi: float) -> str:
        """Interpret MMI value"""
        if mmi < 30:
            return "Oversold - Bullish Signal"
        elif mmi < 40:
            return "Weak - Slightly Bearish"
        elif mmi < 60:
            return "Neutral"
        elif mmi < 70:
            return "Strong - Slightly Bullish"
        else:
            return "Overbought - Bearish Signal"
