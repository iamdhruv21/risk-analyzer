import re
import spacy
from .models import ParsedSignal, SignalType, AssetClass, PriceRange, PriceValue

class FastParser:
    """Fast regex-based signal parser"""

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            print("Downloading spaCy model...")
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=False)
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy model not available. Fast parser will use basic regex only.")
                self.nlp = None

        # Regex patterns for values
        self.patterns = {
            "price": re.compile(r"\b(?:entry|at|cmp|above|near|price|limit|buy at|sell at)\b\s*[:\->\s]*([\d\.\-k\/ ]+)", re.I),
            "tp": re.compile(r"\b(?:tp|targets?|take profit)\b(?:\s+\d{1,2}\b)?[:\->\s]*([\d\.,\-k\/ ]+)", re.I),
            "sl": re.compile(r"\b(?:sl|stop\s*loss|support|stop)\b\s*[:\->\s]*([\d\.,\-k\/ ]+)", re.I),
            "leverage": re.compile(r"(\d+)\s*x", re.I),
        }

    def _parse_numeric(self, val: str) -> float | None:
        """Parse numeric value with k suffix support"""
        if not val:
            return None
        val = val.lower().strip()
        multiplier = 1.0
        if "k" in val:
            multiplier = 1000.0
            val = val.replace("k", "")

        try:
            # Extract just the number part, handling cases like "4692+++"
            match = re.search(r"(\d+\.?\d*)", val)
            if not match:
                return None
            return float(match.group(1)) * multiplier
        except ValueError:
            return None

    def _parse_complex_price(self, val: str) -> PriceValue:
        """Parse price that can be single, range, or list"""
        val = val.strip()

        # Handle ranges like 275-277 or 72k-75k
        if "-" in val and "," not in val:
            parts = val.split("-")
            if len(parts) == 2:
                low = self._parse_numeric(parts[0])
                high = self._parse_numeric(parts[1])
                if low and high:
                    return PriceRange(min=min(low, high), max=max(low, high))

        # Handle arrays like 725-750-775 or 72, 73, 75 or 280/300
        for delimiter in [",", "/", "-"]:
            if delimiter in val:
                parts = [self._parse_numeric(p) for p in val.split(delimiter) if p.strip()]
                clean_parts = [p for p in parts if p is not None]
                if len(clean_parts) > 1:
                    return clean_parts

        return self._parse_numeric(val)

    def _detect_asset_class(self, text: str, asset: str) -> str:
        """Detect asset class from context - returns lowercase string"""
        text_upper = text.upper()
        asset_upper = asset.upper()

        # Crypto indicators
        if any(x in text_upper for x in ["USDT", "BTC", "ETH", "SOL", "XRP", "CRYPTO", "BINANCE"]):
            return "crypto"

        # Forex indicators
        if any(x in text_upper for x in ["GOLD", "XAU", "EURUSD", "GBPUSD", "FOREX", "SILVER"]):
            return "forex"

        # Indices indicators
        if any(x in text_upper for x in ["NIFTY", "BANKNIFTY", "SENSEX", "INDEX"]):
            return "stock"  # Indices mapped to stock

        # Default to stocks
        return "stock"

    def parse(self, text: str) -> ParsedSignal | None:
        """Parse signal from text using fast regex-based extraction"""
        lower_text = text.lower()

        # 1. Extract Signal Type (Intent)
        signal_type = None
        if any(x in lower_text for x in ["buy", "long", "looks good", "above"]):
            signal_type = SignalType.BUY
        elif any(x in lower_text for x in ["sell", "short", "below"]):
            signal_type = SignalType.SELL
        elif "limit" in lower_text:
            signal_type = SignalType.LIMIT

        if not signal_type:
            return None

        # 2. Extract Asset Name
        asset = None
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]

        if lines:
            # Try to find asset in first 2 lines
            for line in lines[:2]:
                lower_line = line.lower()
                # Exclude lines that look like types or common noise
                if any(x in lower_line for x in ["buy", "sell", "trade", "example", "positional", "limit"]):
                    # If line is "Gold Buy Now", extract asset "Gold"
                    clean_line = re.sub(r"\b(buy|sell|now|trade|positional|limit|long|short)\b.*", "", line, flags=re.I).strip()
                    if clean_line:
                        asset = clean_line
                        break
                    continue

                # If it's just a name like "Apollo Micro" or "BTC", take it
                if len(line.split()) <= 3:  # Likely an asset name
                    asset = line
                    break

        # Fallback: Use spaCy to find proper nouns
        if not asset and self.nlp:
            doc = self.nlp(text)
            for token in doc:
                if token.pos_ == "PROPN" and token.text.lower() not in ["buy", "sell", "target", "stoploss", "trade"]:
                    asset = token.text
                    break

        # Last resort: Look for $ or common patterns
        if not asset:
            dollar_match = re.search(r"\$([A-Z]+)", text)
            if dollar_match:
                asset = dollar_match.group(1)

        if not asset:
            return None

        # Clean asset name
        asset = asset.replace("$", "").replace("/", " ").strip()

        # 3. Extract Price (Entry Point)
        price = None
        # Try explicit price patterns
        price_patterns = [
            re.compile(r"\b(?:entry|at|cmp|above|near|price|limit|buy at|sell at)\b\s*[:\->\s]*([\d\.]+k?(?:\s*-\s*[\d\.]+k?)?)", re.I),
        ]

        for pat in price_patterns:
            match = pat.search(text)
            if match:
                res = self._parse_complex_price(match.group(1))
                if isinstance(res, float):
                    price = res
                elif isinstance(res, PriceRange):
                    price = (res.min + res.max) / 2  # Take midpoint
                break

        # Fallback: Look for ranges like "4705-4700"
        if not price:
            range_match = re.search(r"(\d{2,})\s*-\s*(\d{2,})", text)
            if range_match:
                price_res = self._parse_complex_price(range_match.group(0))
                if isinstance(price_res, float):
                    price = price_res
                elif isinstance(price_res, PriceRange):
                    price = (price_res.min + price_res.max) / 2
            else:
                # Look for standalone numbers after Buy/Sell
                standalone = re.search(rf"{signal_type.value}\s*[-\s]*([\d\.]+)", text, re.I)
                if standalone:
                    price = self._parse_numeric(standalone.group(1))

        # 4. Extract Leverage (convert to int, default to 1)
        leverage_match = self.patterns["leverage"].search(text)
        leverage = int(leverage_match.group(1)) if leverage_match else 1

        # 5. Extract Take Profit (TP)
        tp = None
        tp_matches = self.patterns["tp"].findall(text)
        if tp_matches:
            all_tps = []
            for m in tp_matches:
                res = self._parse_complex_price(m)
                if isinstance(res, list):
                    all_tps.extend(res)
                elif res:
                    all_tps.append(res)

            # Deduplicate and sort
            if all_tps:
                unique_tps = []
                for t in all_tps:
                    if isinstance(t, (float, int)) and t not in unique_tps:
                        unique_tps.append(t)
                    elif isinstance(t, PriceRange):
                        unique_tps.append(t)

                tp = unique_tps if len(unique_tps) > 1 else (unique_tps[0] if unique_tps else None)

        # 6. Extract Stop Loss (SL)
        sl = None
        sl_matches = self.patterns["sl"].findall(text)
        if sl_matches:
            all_sls = []
            for m in sl_matches:
                res = self._parse_complex_price(m)
                if isinstance(res, list):
                    all_sls.extend(res)
                elif res:
                    all_sls.append(res)

            sl = all_sls if len(all_sls) > 1 else (all_sls[0] if all_sls else None)

        return ParsedSignal(
            asset=asset,
            assetClass=self._detect_asset_class(text, asset),
            type=signal_type,
            price=price if isinstance(price, float) else None,
            tp=tp,
            sl=sl,
            leverage=leverage
        )
