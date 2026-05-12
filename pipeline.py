#!/usr/bin/env python3
"""
End-to-End Pipeline: Text Signal → Risk Analysis → Feedback

This script connects the signal-parsing and risk-analysis systems.
It reads raw text signals, parses them, and performs risk analysis.

Usage:
    python pipeline.py <signal_file.txt>
    python pipeline.py --interactive
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Optional

from src.parsers import WaterfallParser
from src.analyzer import RiskAnalyzer
from src.utils.signal_adapter import SignalFormatAdapter


class SignalRiskPipeline:
    """End-to-end pipeline from text signal to risk analysis"""

    def __init__(self):
        self.parser = WaterfallParser()
        self.analyzer = RiskAnalyzer()
        self.adapter = SignalFormatAdapter()

    def parse_signal_from_text(self, text: str) -> Optional[dict]:
        """Parse trading signal from raw text"""

        print("\n" + "="*80)
        print("STEP 1: PARSING SIGNAL FROM TEXT")
        print("="*80)

        result = self.parser.process(text)

        if not result.data:
            print(f"❌ Failed to parse signal (latency: {result.latency_ms:.2f}ms)")
            return None

        print(f"✓ Parsed using {result.method.upper()} method")
        print(f"  Latency: {result.latency_ms:.2f}ms")
        print(f"  Confidence: {result.confidence*100:.0f}%")

        parsed_signal = result.data.model_dump()
        print(f"\nParsed Signal:")
        print(json.dumps(parsed_signal, indent=2))

        return parsed_signal

    def convert_signal_format(self, parsed_signal: dict) -> dict:
        """Convert parsed signal to risk-analysis format"""
        print("\n" + "="*80)
        print("STEP 2: CONVERTING SIGNAL FORMAT")
        print("="*80)

        try:
            risk_signal = self.adapter.convert(parsed_signal)
            print("✓ Signal converted successfully")
            print(f"\nRisk Analysis Format:")
            print(json.dumps(risk_signal, indent=2))

            # Validate
            is_valid, error_msg = self.adapter.validate_for_risk_analysis(risk_signal)
            if not is_valid:
                print(f"\n❌ Validation failed: {error_msg}")
                return None

            print("✓ Validation passed")
            return risk_signal

        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            return None

    async def analyze_risk(self, signal: dict) -> Optional[dict]:
        """Perform risk analysis on the signal"""
        print("\n" + "="*80)
        print("STEP 3: RISK ANALYSIS")
        print("="*80)

        try:
            result = await self.analyzer.analyze(signal)
            return result
        except Exception as e:
            print(f"❌ Risk analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def process_text_signal(self, text: str) -> Optional[dict]:
        """Complete pipeline: text → parse → convert → analyze"""
        # Step 1: Parse
        parsed_signal = self.parse_signal_from_text(text)
        if not parsed_signal:
            return None

        # Step 2: Convert
        risk_signal = self.convert_signal_format(parsed_signal)
        if not risk_signal:
            return None

        # Step 3: Analyze
        analysis_result = await self.analyze_risk(risk_signal)
        if not analysis_result:
            return None

        return analysis_result

    async def process_file(self, file_path: str) -> list:
        """Process signals from a text file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            return []

        # Try to detect if file has multiple signals (like signals.txt)
        # Look for "Example N:" pattern
        import re
        examples = re.split(r"Example \d+:", content)
        signals = [s.strip() for s in examples if s.strip()]

        if len(signals) <= 1:
            # Single signal - use entire content
            signals = [content.strip()]

        print(f"\n{'='*80}")
        print(f"PROCESSING FILE: {file_path}")
        print(f"Found {len(signals)} signal(s)")
        print(f"{'='*80}")

        results = []
        for i, signal_text in enumerate(signals, 1):
            print(f"\n{'#'*80}")
            print(f"# SIGNAL {i}/{len(signals)}")
            print(f"{'#'*80}")
            print(f"\nRaw Text:\n{signal_text[:200]}{'...' if len(signal_text) > 200 else ''}\n")

            result = await self.process_text_signal(signal_text)
            if result:
                results.append({
                    "signal_number": i,
                    "raw_text": signal_text,
                    "analysis": result
                })
                print(f"\n✓ Signal {i} processed successfully")
                print(f"  Trade ID: {result.get('trade_id')}")
                print(f"  Decision: {result.get('decision')}")
                print(f"  Composite Score: {result.get('composite_score')}")
            else:
                print(f"\n❌ Signal {i} failed to process")

        return results


def interactive_mode():
    """Interactive mode for entering signals"""
    print("\n" + "="*80)
    print("INTERACTIVE MODE")
    print("="*80)
    print("\nPaste your trading signal below (press Enter twice when done):")
    print("-" * 80)

    lines = []
    empty_count = 0
    while empty_count < 2:
        try:
            line = input()
            if not line.strip():
                empty_count += 1
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break

    signal_text = "\n".join(lines).strip()

    if not signal_text:
        print("No input provided.")
        return

    pipeline = SignalRiskPipeline()
    result = asyncio.run(pipeline.process_text_signal(signal_text))

    if result:
        print("\n" + "="*80)
        print("FINAL RESULT")
        print("="*80)
        print(json.dumps(result, indent=2))
        print(f"\n✓ Analysis complete. Trade ID: {result.get('trade_id')}")
        print(f"\nTo provide feedback:")
        print(f"  python feedback_cli.py {result.get('trade_id')}")
    else:
        print("\n❌ Pipeline failed")


async def main():
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python pipeline.py <signal_file.txt>     # Process file")
        print("  python pipeline.py --interactive         # Interactive input")
        print("\nExamples:")
        print("  python pipeline.py example_signal.txt")
        print("  python pipeline.py my_signals.txt")
        print("  python pipeline.py --interactive")
        sys.exit(1)

    if sys.argv[1] == "--interactive":
        interactive_mode()
        return

    file_path = sys.argv[1]
    pipeline = SignalRiskPipeline()
    results = await pipeline.process_file(file_path)

    print("\n" + "="*80)
    print("PIPELINE SUMMARY")
    print("="*80)
    print(f"Total Signals: {len(results)}")
    print(f"Successful: {len(results)}")
    print()

    for r in results:
        analysis = r["analysis"]
        print(f"Signal {r['signal_number']}:")
        print(f"  Trade ID: {analysis.get('trade_id')}")
        print(f"  Asset: {analysis.get('signal', {}).get('asset')}")
        print(f"  Decision: {analysis.get('decision')}")
        print(f"  Score: {analysis.get('composite_score')}")
        print()

    if results:
        print("\nNext steps:")
        print("1. Review decisions in audit_log.jsonl")
        print("2. Execute trades (if approved)")
        print("3. Provide feedback:")
        print(f"   python feedback_cli.py <trade_id>")


if __name__ == "__main__":
    asyncio.run(main())
