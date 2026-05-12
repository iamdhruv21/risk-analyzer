#!/usr/bin/env python3
"""Test the signal parser directly"""

from src.parsers import WaterfallParser

def test_parser():
    parser = WaterfallParser()
    
    test_signals = [
        "BTC Buy 65000\nTP 68000\nSL 63500\nLeverage 10x",
        "Gold Buy 4700-4705\nSl 4692\nTp 4710/4715/4720",
        "$BTC/USDT\nLIMIT ENTRY->73.5K\nTP->72K, 70K, 69K\nSL->75K\nLV->3-5X"
    ]
    
    for i, signal_text in enumerate(test_signals, 1):
        print(f"\n{'='*80}")
        print(f"Test Signal {i}")
        print(f"{'='*80}")
        print(f"Input:\n{signal_text}\n")
        
        result = parser.process(signal_text)
        
        if result.data:
            print(f"✓ Parsed using {result.method.upper()} method")
            print(f"  Latency: {result.latency_ms:.2f}ms")
            print(f"  Confidence: {result.confidence*100:.0f}%")
            print(f"\nParsed Data:")
            print(f"  Asset: {result.data.asset}")
            print(f"  Type: {result.data.type}")
            print(f"  Asset Class: {result.data.assetClass}")
            print(f"  Price: {result.data.price}")
            print(f"  TP: {result.data.tp}")
            print(f"  SL: {result.data.sl}")
            print(f"  Leverage: {result.data.leverage}")
        else:
            print(f"❌ Failed to parse")
            print(f"  Latency: {result.latency_ms:.2f}ms")

if __name__ == "__main__":
    test_parser()
