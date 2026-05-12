# Argus Risk Analysis System

A production-ready, multi-layered AI-powered risk analysis system for evaluating trade signals across crypto, forex, stocks, and commodities. Built with a microservices-inspired architecture using specialized agents and deterministic rule gates.

## Overview

Argus Risk Analysis processes incoming trade signals through a 6-layer pipeline that combines deterministic rules, real-time market data, specialized AI agents, and LLM-based synthesis to produce actionable risk assessments.

**Key Features:**
- Multi-layer risk validation (fast rules → specialized agents → LLM synthesis)
- Real-time market data integration (Binance, Alpha Vantage)
- Specialized agents for technical analysis, sentiment, metrics, and volatility
- LLM-powered risk synthesis using Claude
- Comprehensive audit logging for all decisions
- Production-ready with strict data validation and error handling

## Architecture

### 6-Layer Pipeline

```
Layer 0: Signal Validation
    ↓
Layer 1: Context Aggregation (Market Data, News, Sentiment)
    ↓
Layer 2: Fast Rule Engine (Deterministic Gates)
    ↓
Layer 3: Specialized Sub-Agents (Parallel Analysis)
    ↓
Layer 4: LLM Orchestration (Risk Synthesis)
    ↓
Layer 5: Decision Gate (Final Override)
    ↓
Layer 6: Structured Output & Audit Logging
```

### Layer Details

#### **Layer 0: Signal Validation**
Validates incoming trade signals using Pydantic models. Ensures all required fields (asset, type, price, tp, sl, leverage) are present and within acceptable ranges.

**File:** `src/models/signal.py`

#### **Layer 1: Context Aggregation**
Fetches real-time data from multiple sources in parallel:
- Market data (OHLCV, price, volume) from Binance
- News sentiment from Alpha Vantage
- Economic calendar events
- Portfolio state (account balance, positions)
- Sentiment indicators (Fear & Greed, MMI, VIX)

**File:** `src/services/context_aggregator.py`

**Important:** Returns `None` for any data source that is unavailable. No mock data in production.

#### **Layer 2: Fast Rule Engine**
Deterministic gates that reject trades immediately if they violate hard constraints:
- Minimum R:R ratio (1.5x)
- Maximum leverage limits (10x for crypto, 50x for forex)
- Daily drawdown caps
- Stop loss distance validation (ATR-based)

**File:** `src/services/rule_engine.py`

#### **Layer 3: Specialized Sub-Agents**
Four specialized agents run in parallel, each analyzing different aspects:

1. **Technical Agent** (`src/agents/technical_agent.py`)
   - RSI, EMA, ADX indicators
   - Trend alignment analysis
   - Requires OHLCV data (minimum 14 bars)

2. **Sentiment Agent** (`src/agents/sentiment_agent.py`)
   - News sentiment analysis with inverse correlation detection
   - Fear & Greed Index (contrarian signals)
   - MMI (Market Movement Insight)
   - Market regime alignment
   - High-impact event detection

3. **Metrics Agent** (`src/agents/metrics_agent.py`)
   - R:R ratio validation
   - Liquidation risk calculation
   - Position sizing recommendations

4. **Volatility Agent** (`src/agents/volatility_agent.py`)
   - VIX analysis (global volatility)
   - India VIX (for Indian market assets)
   - ATR-based stop loss validation
   - Market regime analysis

Each agent returns a score (0-100) and reasoning. If critical data is unavailable, agents return `score: None`.

#### **Layer 4: LLM Orchestration (Risk Synthesis)**
Claude-powered synthesis engine that aggregates all agent reports into a unified risk assessment.

**File:** `src/agents/synthesis_agent.py`

**Behavior:**
- If Anthropic API key is configured: Uses Claude to synthesize reports
- If API key missing: Falls back to weighted average (Technical: 30%, Metrics: 30%, Volatility: 25%, Sentiment: 15%)
- Returns `composite_score: None` if any agent has invalid/missing scores

**Model:** `claude-3-5-sonnet-20241022`

#### **Layer 5: Decision Gate**
Maps composite scores to discrete actions with hard overrides:

| Score Range | Decision | Description |
|-------------|----------|-------------|
| 75-100 | APPROVE | High confidence, all indicators aligned |
| 50-74 | ADJUST | Moderate confidence, consider position size reduction |
| 30-49 | FLAG | Low confidence, requires manual review |
| 0-29 | REJECT | Very low confidence, too risky to execute |

**Hard Overrides:**
- R:R ratio below 1.5x → immediate REJECT
- Composite score is `None` → immediate REJECT

**File:** `src/services/decision_gate.py`

#### **Layer 6: Audit Logging**
Persists all decisions to JSONL file with full context for reproducibility.

**File:** `src/services/audit_logger.py`
**Output:** `audit_log.jsonl`

## Project Structure

```
risk-analysis/
├── src/
│   ├── analyzer.py                  # Main orchestrator
│   ├── models/
│   │   └── signal.py                # Pydantic models (TradeSignal, RiskContext, RiskAnalysisReport)
│   ├── services/
│   │   ├── context_aggregator.py    # Layer 1: Data fetching
│   │   ├── rule_engine.py           # Layer 2: Fast rules
│   │   ├── decision_gate.py         # Layer 5: Final decision
│   │   └── audit_logger.py          # Layer 6: Logging
│   └── agents/
│       ├── technical_agent.py       # Layer 3: Technical analysis
│       ├── sentiment_agent.py       # Layer 3: Sentiment analysis
│       ├── metrics_agent.py         # Layer 3: Risk metrics
│       ├── volatility_agent.py      # Layer 3: Volatility analysis
│       └── synthesis_agent.py       # Layer 4: LLM synthesis
├── main.py                          # Entry point
├── .env                             # API keys configuration
├── pyproject.toml                   # Dependencies
└── audit_log.jsonl                  # Decision audit trail
```

## Installation

### Prerequisites
- Python 3.12+
- UV package manager (recommended) or pip

### Setup

1. Clone the repository:
```bash
cd /var/www/Projects/Argus/risk-analysis
```

2. Install dependencies:
```bash
uv sync
```

Or with pip:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
# Required for market data
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Required for news sentiment
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Required for LLM synthesis (optional fallback to weighted average)
ANTHROPIC_API_KEY=your_anthropic_key
```

## Configuration

### API Keys

| Service | Required | Purpose | Get Key |
|---------|----------|---------|---------|
| Binance | Yes | Market data, portfolio state | [binance.com/api-management](https://www.binance.com/api-management) |
| Alpha Vantage | Yes | News sentiment | [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key) |
| Anthropic | Optional | LLM synthesis (falls back to weighted average) | [console.anthropic.com](https://console.anthropic.com) |

### Risk Parameters

Edit thresholds in:
- `src/services/rule_engine.py` - Hard rule limits (R:R, leverage, drawdown)
- `src/services/decision_gate.py` - Score-to-decision mapping
- `src/agents/synthesis_agent.py` - Agent weighting (if no LLM)

## Usage

### Basic Example

```python
import asyncio
from src.analyzer import RiskAnalyzer

async def analyze_trade():
    analyzer = RiskAnalyzer()
    
    signal = {
        "asset": "BTC",
        "assetClass": "crypto",
        "type": "BUY",
        "price": 65000,
        "tp": 68000,
        "sl": 63500,
        "leverage": 10
    }
    
    result = await analyzer.analyze(signal)
    print(result)

asyncio.run(analyze_trade())
```

### Running the Example

```bash
python main.py
```

### Sample Output

```json
{
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
  "rationale": "Strong technical alignment with bullish trend, acceptable R:R ratio (1.67x), moderate volatility environment. All agents in agreement.",
  "metrics": {
    "rr_ratio": 1.67,
    "liquidation_risk": "low"
  },
  "agent_reports": {
    "technical": {"score": 80, "reasoning": "..."},
    "sentiment": {"score": 75, "reasoning": "..."},
    "metrics": {"score": 70, "reasoning": "..."},
    "volatility": {"score": 85, "reasoning": "..."}
  },
  "suggested_adjustments": {
    "leverage": 8,
    "position_size_multiplier": 0.8
  }
}
```

## Error Handling

### Missing Data Behavior

The system follows strict production guidelines:
- **No mock data**: All data sources return `None` when unavailable
- **Fail fast**: Agents return `score: None` if critical data is missing
- **Automatic rejection**: Trades with insufficient data are rejected at Layer 4/5

### Common Scenarios

1. **Binance API keys not configured**
   - Market data returns `None`
   - Technical agent returns `score: None`
   - Trade rejected: "Insufficient data for risk assessment"

2. **Alpha Vantage API key missing**
   - News data returns `None`
   - Sentiment agent may still function with other sentiment sources
   - If all sentiment sources unavailable, agent returns `score: None`

3. **Anthropic API key missing**
   - Synthesis falls back to weighted average
   - Warning added to output: "LLM Synthesis skipped - API key not configured"
   - Trade still processed if all agent scores are valid

## Development

### Adding a New Agent

1. Create file in `src/agents/your_agent.py`
2. Implement `analyze(signal, context)` method
3. Return `{"score": 0-100, "reasoning": "...", ...}`
4. Add to `src/analyzer.py` agent execution
5. Update synthesis weights if using fallback mode

### Testing

```bash
# Run with example signal
python main.py

# Check audit logs
tail -n 1 audit_log.jsonl | jq
```

### Debugging

Enable verbose output:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Deployment

### Checklist

- [ ] All API keys configured in `.env`
- [ ] Verify Binance API permissions (read-only for portfolio, trading disabled)
- [ ] Test with live data (not paper trading keys)
- [ ] Set up monitoring for `audit_log.jsonl`
- [ ] Configure log rotation
- [ ] Set up alerting for REJECT decisions
- [ ] Review and adjust risk thresholds per trading strategy

### Security

- Never commit `.env` file
- Use read-only API keys where possible
- Rotate API keys regularly
- Monitor audit logs for suspicious activity
- Run in isolated environment with network restrictions

### Performance

- Average latency: ~2-3 seconds per trade analysis
- Bottleneck: External API calls (Binance, Alpha Vantage)
- Optimization: Consider caching market data for high-frequency analysis
- Scaling: Run multiple instances with load balancer

## Dependencies

Core libraries:
- `anthropic` - Claude LLM integration
- `ccxt` - Crypto exchange API wrapper
- `aiohttp` - Async HTTP client
- `pandas` - Data analysis
- `pandas-ta` - Technical indicators
- `pydantic` - Data validation
- `python-dotenv` - Environment configuration

See `pyproject.toml` for complete list.

## Audit Trail

All decisions are logged to `audit_log.jsonl` with:
- Complete signal details
- All context data (market, news, sentiment)
- Agent scores and reasoning
- Composite score and LLM rationale
- Final decision and suggested adjustments
- Timestamp

Format: One JSON object per line (JSONL)

### Querying Audit Logs

```bash
# Last 10 decisions
tail -n 10 audit_log.jsonl | jq -r '.decision'

# All REJECT decisions
grep '"decision":"REJECT"' audit_log.jsonl | jq

# Average composite score
jq -s '[.[].composite_score] | add/length' audit_log.jsonl
```

## Limitations

- **Economic calendar**: Not currently integrated (returns `None`)
- **India VIX**: Requires separate data source (returns `None` from sentiment endpoint)
- **Multi-TP/SL**: Supported in model but only first value used in calculations
- **Portfolio state**: Only USDT balance fetched from Binance

## Roadmap

- [ ] Economic calendar integration (Forex Factory, Trading Economics)
- [ ] India VIX data source (NSE API)
- [ ] Multi-TP/SL support in agents
- [ ] PostgreSQL/TimescaleDB backend for audit logs
- [ ] Prometheus metrics export
- [ ] Backtesting framework
- [ ] Web dashboard for monitoring
- [ ] Webhook support for external integrations

## License

Proprietary - Argus Project

## Support

For issues or questions:
1. Check audit logs: `audit_log.jsonl`
2. Review error messages in console output
3. Verify API key configuration
4. Test with minimal example in `main.py`

---

**Last Updated:** 2026-05-12
**Version:** 1.0.0 (Production Ready)
