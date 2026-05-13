#!/usr/bin/env python3
"""
Argus Risk Analysis - Main Entry Point

This is the single entry point for the entire system.
It handles:
1. Signal parsing from text files
2. Format conversion
3. 6-layer risk analysis
4. Decision output

Usage:
    uv run main.py <signal_file.txt>
    uv run main.py --interactive
    uv run main.py --example
"""

import sys
import json
import asyncio
import re
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.parsers import WaterfallParser
from src.analyzer import RiskAnalyzer


class ArgusRiskAnalysis:
    """Main application orchestrator"""

    def __init__(self, source_filename: str = None):
        self.parser = WaterfallParser()
        self.analyzer = RiskAnalyzer(source_filename=source_filename)
        self.source_filename = source_filename

    def parse_signal_from_text(self, text: str) -> Optional[dict]:
        """Parse trading signal from raw text - output format ready for risk analysis"""
        print("\n" + "="*80)
        print("STEP 1: PARSING SIGNAL")
        print("="*80)

        result = self.parser.process(text)

        if not result.data:
            print(f"❌ Failed to parse signal (latency: {result.latency_ms:.2f}ms)")
            return None

        print(f"✓ Parsed using {result.method.upper()} method")
        print(f"  Latency: {result.latency_ms:.2f}ms")
        print(f"  Confidence: {result.confidence*100:.0f}%")

        # Validate required fields
        if not result.data.price or not result.data.tp or not result.data.sl:
            print(f"❌ Incomplete signal: price={result.data.price}, tp={result.data.tp}, sl={result.data.sl}")
            return None

        parsed_signal = result.data.model_dump()
        print(f"\nParsed Signal (ready for analysis):")
        print(json.dumps(parsed_signal, indent=2))
        print("✓ Validation passed")

        return parsed_signal

    async def analyze_risk(self, signal: dict) -> Optional[dict]:
        """Perform risk analysis on the signal"""
        print("\n" + "="*80)
        print("STEP 2: RISK ANALYSIS")
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
        """Complete pipeline: text → parse → analyze"""
        # Step 1: Parse (output format ready for risk analysis)
        parsed_signal = self.parse_signal_from_text(text)
        if not parsed_signal:
            return None

        # Step 2: Analyze
        analysis_result = await self.analyze_risk(parsed_signal)
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

        # Try to detect if file has multiple signals (like Example 1:, Example 2:)
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

    def print_summary(self, results: list):
        """Print summary of processed signals"""
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total Signals Processed: {len(results)}")
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
            print("1. Review decisions in output/ folder")
            print("2. Execute trades if approved")
            print("3. Provide feedback after execution:")
            print(f"   uv run feedback_cli.py <trade_id>")


async def interactive_mode():
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

    app = ArgusRiskAnalysis(source_filename="interactive_input")
    result = await app.process_text_signal(signal_text)

    if result:
        print("\n" + "="*80)
        print("FINAL RESULT")
        print("="*80)
        print(json.dumps(result, indent=2, default=str))
        print(f"\n✓ Analysis complete. Trade ID: {result.get('trade_id')}")
        print(f"\nTo provide feedback:")
        print(f"  python feedback_cli.py {result.get('trade_id')}")
    else:
        print("\n❌ Analysis failed")


async def example_mode():
    """Run with example signal"""
    example_signal = """BTC Buy 65000
TP 68000
SL 63500
Leverage 10x"""

    print("\n" + "="*80)
    print("EXAMPLE MODE")
    print("="*80)
    print(f"\nProcessing example signal:\n{example_signal}\n")

    app = ArgusRiskAnalysis(source_filename="example_signal")
    result = await app.process_text_signal(example_signal)

    if result:
        print("\n" + "="*80)
        print("FINAL RESULT")
        print("="*80)
        print(json.dumps(result, indent=2, default=str))
        print(f"\n✓ Example complete. Trade ID: {result.get('trade_id')}")
    else:
        print("\n❌ Example failed")


def get_first_file_from_input() -> Optional[Path]:
    """Get the first file from input folder"""
    input_dir = Path("input")
    input_dir.mkdir(exist_ok=True)

    # Get all files (not directories, not hidden files)
    files = [f for f in input_dir.iterdir() if f.is_file() and not f.name.startswith('.')]

    if not files:
        return None

    # Return first file (sorted alphabetically)
    return sorted(files)[0]


def move_to_completed(file_path: Path):
    """Move processed file to completed folder"""
    completed_dir = Path("completed")
    completed_dir.mkdir(exist_ok=True)

    # Generate destination filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    dest_path = completed_dir / dest_filename

    shutil.move(str(file_path), str(dest_path))
    print(f"\n✓ Moved processed file to: {dest_path}")


async def main():
    """Main entry point"""
    # Check if any arguments provided
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--interactive":
            await interactive_mode()
            return

        if arg == "--example":
            await example_mode()
            return

        # Process specific file (old behavior)
        file_path = arg
        app = ArgusRiskAnalysis(source_filename=Path(file_path).name)
        results = await app.process_file(file_path)
        app.print_summary(results)
        return

    # No arguments - check input folder
    print("\n" + "="*80)
    print("ARGUS RISK ANALYSIS SYSTEM - AUTO MODE")
    print("="*80)
    print("\nChecking input folder for files...")

    input_file = get_first_file_from_input()

    if not input_file:
        print("\n✗ No files to process in input folder")
        print("\nUsage:")
        print("  uv run main.py                       # Auto-process from input folder")
        print("  uv run main.py <signal_file.txt>     # Process specific file")
        print("  uv run main.py --interactive         # Interactive input")
        print("  uv run main.py --example             # Run example")
        print("\nTo process files automatically:")
        print("  1. Place signal files in the 'input' folder")
        print("  2. Run: uv run main.py")
        print("  3. Results will be in 'output' folder")
        print("  4. Processed files moved to 'completed' folder")
        print()
        return

    print(f"\n✓ Found file: {input_file.name}")

    # Process the file
    app = ArgusRiskAnalysis(source_filename=input_file.name)
    results = await app.process_file(str(input_file))
    app.print_summary(results)

    # Move to completed folder
    if results:
        move_to_completed(input_file)

if __name__ == "__main__":
    asyncio.run(main())
