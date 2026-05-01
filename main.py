import asyncio
from src.analyzer import run_example

if __name__ == "__main__":
    # The input variable requested by the user
    resultJson = {
        "asset": "BTC",
        "assetClass": "crypto",
        "type": "BUY",
        "price": 65000,
        "tp": 68000,
        "sl": 63500,
        "leverage": 10
    }
    
    # Executing Phase 1
    asyncio.run(run_example(resultJson))
