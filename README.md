# Argus Risk Analysis System

Production-ready AI-powered risk analysis for trading signals with Human-in-the-Loop reinforcement learning.

## Quick Start

### 1. Install

```bash
# Install UV (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Pipeline

```bash
# Process signals from text file
uv run python pipeline.py ../signal-parsing/signals.txt

# Interactive mode
uv run python pipeline.py --interactive
```

### 4. Provide Feedback

```bash
# After trade execution
uv run python feedback_cli.py <trade_id>

# View statistics
uv run python feedback_query.py summary
```

## Features

- **Integrated Signal Parser** - Waterfall approach (Fast regex → LLM fallback)
- **6-Layer Risk Analysis** - Validation → Context → Rules → Agents → Synthesis → Decision
- **Real-time Market Data** - Binance, Alpha Vantage integration
- **Specialized AI Agents** - Technical, Sentiment, Metrics, Volatility
- **LLM-Powered Synthesis** - Claude-based risk assessment
- **HITL Feedback System** - Continuous learning from human experts
- **Production-Ready** - No mock data, proper error handling, audit trails

## Documentation

- [Complete Documentation](.agent/README.md) - Full system guide
- [Pipeline Guide](.agent/PIPELINE_GUIDE.md) - Text-to-analysis workflow
- [Parser Implementation](.agent/PARSER_IMPLEMENTATION.md) - Signal parsing details
- [HITL Guide](.agent/HITL_GUIDE.md) - Feedback system usage
- [Implementation Summary](.agent/IMPLEMENTATION_SUMMARY.md) - Development details

## Workflow

```
Text Signal → Parse → Convert → Analyze → Decision → Execute → Feedback → Learn
```

## Project Structure

```
├── src/                    # Core system
│   ├── analyzer.py         # Main orchestrator
│   ├── agents/             # Specialized agents
│   ├── services/           # Core services
│   └── utils/              # Signal adapter
├── pipeline.py             # End-to-end pipeline
├── feedback_cli.py         # Feedback submission
├── feedback_query.py       # Feedback analytics
├── .agent/                 # Documentation
└── .env                    # Configuration
```

## Requirements

- Python 3.12+
- UV package manager
- API Keys: Binance, Alpha Vantage, Anthropic (optional)

## License

Proprietary - Argus Project

## Support

See [documentation](.agent/README.md) for detailed guides and troubleshooting.

---

**Version:** 1.1.0  
**Status:** ✅ Production Ready + HITL Enabled
