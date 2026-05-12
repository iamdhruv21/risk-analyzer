import time
from .models import ParsingResult, ParsedSignal
from .fast_parser import FastParser
from .intelligence_parser import IntelligenceParser

class WaterfallParser:
    """
    Orchestrator that implements waterfall parsing strategy:
    1. Try Fast Parser (regex-based) first
    2. If incomplete (missing price, tp, or sl), fallback to Intelligence Parser (LLM)
    """

    def __init__(self):
        print("Initializing WaterfallParser...")
        self.fast = FastParser()
        self.intelligence = IntelligenceParser()
        print("WaterfallParser ready.")

    def _is_complete(self, signal: ParsedSignal | None) -> bool:
        """Check if signal has all critical fields"""
        if not signal:
            return False

        # Critical fields: asset, type, price, tp, sl
        # If any of these are None, signal is incomplete
        is_complete = all([
            signal.asset is not None,
            signal.type is not None,
            signal.price is not None,
            signal.tp is not None,
            signal.sl is not None
        ])

        return is_complete

    def process(self, text: str) -> ParsingResult:
        """
        Process text signal using waterfall approach:
        Fast → Intelligence
        """
        start_time = time.perf_counter()

        # Step 1: Try Fast Parser
        try:
            signal = self.fast.parse(text)

            if signal and self._is_complete(signal):
                # Fast parser succeeded with complete data
                latency = (time.perf_counter() - start_time) * 1000
                return ParsingResult(
                    data=signal,
                    latency_ms=latency,
                    method="fast",
                    confidence=0.9
                )

            # Fast parser returned incomplete signal - fallback to intelligence
            if signal:
                print(f"Fast parser incomplete: price={signal.price}, tp={signal.tp}, sl={signal.sl}")

        except Exception as e:
            print(f"Fast parser error: {e}")

        # Step 2: Fallback to Intelligence Parser
        print("Falling back to Intelligence Parser...")
        signal = self.intelligence.parse(text)
        latency = (time.perf_counter() - start_time) * 1000

        if signal:
            return ParsingResult(
                data=signal,
                latency_ms=latency,
                method="intelligence",
                confidence=0.95
            )

        # Both parsers failed
        return ParsingResult(
            data=None,
            latency_ms=latency,
            method="fast",
            confidence=0.0
        )
