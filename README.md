# Argus Risk Analysis System

Production-ready AI-powered risk analysis for trading signals with Human-in-the-Loop reinforcement learning.

## Quick Start

### 1. Install

```bash
# Install UV package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Download NLP model
uv run python -m spacy download en_core_web_sm
```

### 2. Configure (Optional)

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run

```bash
# Process signal from file
uv run python main.py example_signal.txt

# Interactive mode
uv run python main.py --interactive

# Run example
uv run python main.py --example
```

### 4. Provide Feedback

```bash
# After trade execution
uv run python feedback_cli.py <trade_id>

# View statistics
uv run python feedback_query.py summary
```

## Single Entry Point

**`main.py`** - The only entry point for risk analysis

```bash
# Process file (single or multiple signals)
uv run main.py signals.txt

# Interactive mode - paste signal text
uv run main.py --interactive

# Run built-in example
uv run main.py --example
```

**Feedback Tools** (separate):
- `feedback_cli.py` - Submit feedback on trades
- `feedback_query.py` - Query and analyze feedback

## Features

- **Integrated Signal Parser** - Waterfall approach (Fast regex → LLM fallback)
- **6-Layer Risk Analysis** - Validation → Context → Rules → Agents → Synthesis → Decision
- **Real-time Market Data** - Binance, Alpha Vantage integration
- **Specialized AI Agents** - Technical, Sentiment, Metrics, Volatility
- **LLM-Powered Synthesis** - Claude-based risk assessment
- **HITL Feedback System** - Continuous learning from human experts
- **Production-Ready** - No mock data, proper error handling, audit trails

## Workflow

```
Text Signal (txt file)
    ↓
main.py (single entry point)
    ├─ Parse Signal (Fast → Intelligence)
    ├─ Convert Format
    └─ Risk Analysis (6 layers)
    ↓
Decision (APPROVE/ADJUST/FLAG/REJECT)
    ↓
audit_log.jsonl
    ↓
Execute Trade
    ↓
feedback_cli.py (provide feedback)
    ↓
feedback_log.jsonl
    ↓
Continuous Learning
```

## Example Signal

Create `my_signal.txt`:
```
BTC Buy 65000
TP 68000
SL 63500
Leverage 10x
```

Run:
```bash
uv run main.py my_signal.txt
```

## Documentation

- [Complete Guide](.agent/README.md) - Full system documentation
- [Pipeline Guide](.agent/PIPELINE_GUIDE.md) - Text-to-analysis workflow
- [Parser Details](.agent/PARSER_IMPLEMENTATION.md) - Signal parsing
- [HITL Guide](.agent/HITL_GUIDE.md) - Feedback system
- [Quick Start](QUICK_START.md) - 5-minute setup

## Project Structure

```
├── main.py                     # ⭐ SINGLE ENTRY POINT
├── feedback_cli.py             # Feedback submission
├── feedback_query.py           # Feedback analytics
├── src/
│   ├── parsers/                # Signal parsing (Fast + Intelligence)
│   ├── agents/                 # Specialized analysis agents
│   ├── services/               # Core services
│   ├── models/                 # Data models
│   └── utils/                  # Format adapter
├── .agent/                     # Documentation
└── .env                        # Configuration
```

## Requirements

- Python 3.12+
- UV package manager
- API Keys:
  - **Required**: Anthropic Claude (risk synthesis)
  - **Optional**: Groq, Binance, Alpha Vantage
  - **FREE (no key)**: Fear & Greed Index, VIX

See [API Keys Guide](.agent/API_KEYS.md) for detailed setup instructions.

## Usage Examples

### Process File

```bash
# Single signal
echo "BTC Buy 65000, TP 68000, SL 63500" > signal.txt
uv run main.py signal.txt

# Multiple signals
uv run main.py signals_batch.txt
```

### Interactive Mode

```bash
uv run main.py --interactive
# Paste your signal, press Enter twice
```

### Example Mode

```bash
uv run main.py --example
# Runs built-in BTC example
```

### Feedback

```bash
# List recent trades
uv run feedback_cli.py

# Submit feedback for specific trade
uv run feedback_cli.py a1b2c3d4-...

# View aggregated statistics
uv run feedback_query.py summary

# Export training data
uv run feedback_query.py export ml_data.json
```

## Output

```json
{
  "trade_id": "a1b2c3d4-...",
  "signal": {
    "asset": "BTC",
    "type": "BUY",
    "price": 65000,
    "tp": 68000,
    "sl": 63500,
    "leverage": 10
  },
  "decision": "APPROVE",
  "composite_score": 78.5,
  "rationale": "Strong technical alignment...",
  "metrics": {"rr_ratio": 1.67},
  "agent_reports": {...},
  "suggested_adjustments": {...}
}
```

## License

Proprietary - Argus Project

## Support

See [documentation](.agent/README.md) for detailed guides and troubleshooting.

---

**Version:** 1.2.0  
**Status:** ✅ Production Ready + HITL Enabled  
**Entry Point:** `main.py` (single)
