import os
import instructor
from groq import Groq
from .models import ParsedSignal

class IntelligenceParser:
    """LLM-based fallback parser using Groq/Llama"""

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

        if not self.groq_api_key or self.groq_api_key == "your_groq_key_here":
            self.client = None
            print("Warning: GROQ_API_KEY not configured. Intelligence parser disabled.")
        else:
            try:
                self.client = instructor.from_groq(
                    Groq(api_key=self.groq_api_key)
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client: {e}")
                self.client = None

    def parse(self, text: str) -> ParsedSignal | None:
        """Parse signal using LLM when fast parser fails"""
        if not self.client:
            return None

        system_prompt = """You are a specialized trade signal parser.
Extract trading signal details from the provided text into structured JSON format.

IMPORTANT: Output format must match risk analyzer schema exactly:

Guidelines:
- asset: The trading instrument (e.g., BTC, GOLD, NIFTY)
- assetClass: Must be lowercase: "crypto", "forex", "stock", or "commodity"
- type: BUY, SELL, or LIMIT
- price: Entry price (single number, use midpoint if range)
- tp: Take profit target(s) - can be single number or array
- sl: Stop loss level(s) - can be single number or array
- leverage: Integer (1-125), default to 1 if not specified

If a field is unclear or missing, use null.
For multiple TPs or SLs, return as an array.
"""

        try:
            result = self.client.chat.completions.create(
                model=self.model_name,
                response_model=ParsedSignal,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                max_tokens=500,
                temperature=0,
            )

            return result

        except Exception as e:
            print(f"Intelligence parser error: {e}")
            return None
