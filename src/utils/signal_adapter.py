"""
Adapter to convert signal-parsing format to risk-analysis format.
Handles different field names and data structures between the two systems.
"""

from typing import Dict, Any, Union, List

class SignalFormatAdapter:
    """Converts signal-parsing TradeSignal to risk-analysis format"""

    ASSET_CLASS_MAP = {
        "CRYPTO": "crypto",
        "FOREX": "forex",
        "STOCKS": "stock",
        "INDICES": "stock",
    }

    SIGNAL_TYPE_MAP = {
        "BUY": "BUY",
        "SELL": "SELL",
        "LIMIT": "BUY",  # Assume LIMIT is BUY unless specified
        "AMEND": "BUY",  # Default to BUY
    }

    @staticmethod
    def extract_price_value(price_value: Union[float, List[float], Dict, None]) -> float:
        """Extract a single float from various price formats"""
        if price_value is None:
            return None

        if isinstance(price_value, (int, float)):
            return float(price_value)

        if isinstance(price_value, list):
            return float(price_value[0]) if price_value else None

        if isinstance(price_value, dict):
            if 'min' in price_value and 'max' in price_value:
                return (float(price_value['min']) + float(price_value['max'])) / 2

        return None

    @staticmethod
    def extract_tp_list(tp_value: Union[float, List[float], Dict, None]) -> Union[float, List[float]]:
        """Extract TP as single value or list"""
        if tp_value is None:
            return None

        if isinstance(tp_value, (int, float)):
            return float(tp_value)

        if isinstance(tp_value, list):
            return [float(x) for x in tp_value] if len(tp_value) > 1 else float(tp_value[0])

        if isinstance(tp_value, dict):
            if 'min' in tp_value and 'max' in tp_value:
                return [float(tp_value['min']), float(tp_value['max'])]

        return None

    @staticmethod
    def extract_sl_list(sl_value: Union[float, List[float], Dict, None]) -> Union[float, List[float]]:
        """Extract SL as single value or list"""
        if sl_value is None:
            return None

        if isinstance(sl_value, (int, float)):
            return float(sl_value)

        if isinstance(sl_value, list):
            return [float(x) for x in sl_value] if len(sl_value) > 1 else float(sl_value[0])

        if isinstance(sl_value, dict):
            if 'min' in sl_value and 'max' in sl_value:
                return [float(sl_value['min']), float(sl_value['max'])]

        return None

    @classmethod
    def convert(cls, parsed_signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert signal-parsing format to risk-analysis format.

        Input format (from signal-parsing):
        {
            "type": "BUY",
            "asset": "BTC",
            "assetClass": "CRYPTO",
            "price": 73500.0,
            "leverage": 5.0,
            "tp": [72000, 70000, 69000] or 72000,
            "sl": 75000 or [75000]
        }

        Output format (for risk-analysis):
        {
            "asset": "BTC",
            "assetClass": "crypto",
            "type": "BUY",
            "price": 73500.0,
            "tp": [72000, 70000, 69000] or 72000,
            "sl": 75000,
            "leverage": 5
        }
        """

        if not parsed_signal:
            raise ValueError("Parsed signal is None or empty")

        # Extract values
        asset = parsed_signal.get("asset")
        if not asset:
            raise ValueError("Asset is required")

        asset_class = parsed_signal.get("assetClass")
        if not asset_class:
            raise ValueError("Asset class is required")

        signal_type = parsed_signal.get("type")
        if not signal_type:
            raise ValueError("Signal type is required")

        # Convert asset class
        asset_class_lower = cls.ASSET_CLASS_MAP.get(asset_class, asset_class.lower())

        # Convert signal type
        type_converted = cls.SIGNAL_TYPE_MAP.get(signal_type, signal_type)

        # Extract price (entry price)
        price = cls.extract_price_value(parsed_signal.get("price"))
        if price is None:
            raise ValueError("Price is required for risk analysis")

        # Extract TP and SL
        tp = cls.extract_tp_list(parsed_signal.get("tp"))
        sl = cls.extract_sl_list(parsed_signal.get("sl"))

        if tp is None:
            raise ValueError("Take Profit (TP) is required for risk analysis")
        if sl is None:
            raise ValueError("Stop Loss (SL) is required for risk analysis")

        # Extract leverage (default to 1 if not specified)
        leverage = parsed_signal.get("leverage")
        if leverage is None:
            leverage = 1
        leverage = int(leverage)

        return {
            "asset": asset,
            "assetClass": asset_class_lower,
            "type": type_converted,
            "price": price,
            "tp": tp,
            "sl": sl,
            "leverage": leverage
        }

    @classmethod
    def validate_for_risk_analysis(cls, signal: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate that the signal has all required fields for risk analysis.
        Returns (is_valid, error_message)
        """
        required_fields = ["asset", "assetClass", "type", "price", "tp", "sl", "leverage"]

        for field in required_fields:
            if field not in signal or signal[field] is None:
                return False, f"Missing required field: {field}"

        # Validate types
        if not isinstance(signal["asset"], str):
            return False, "Asset must be a string"

        if signal["assetClass"] not in ["crypto", "forex", "stock", "commodity"]:
            return False, f"Invalid assetClass: {signal['assetClass']}"

        if signal["type"] not in ["BUY", "SELL"]:
            return False, f"Invalid type: {signal['type']}"

        if not isinstance(signal["price"], (int, float)):
            return False, "Price must be a number"

        if not isinstance(signal["leverage"], int) or signal["leverage"] < 1 or signal["leverage"] > 125:
            return False, "Leverage must be an integer between 1 and 125"

        return True, ""
