# HermesTradingAgents 🧠📈

**Multi-agent LLM trading framework — Hermes Agent compatible.**

Fork adapté de [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) (MIT).
Intégration native avec **Hermes Agent** via MCP + DeepSeek par défaut.

## What's different from upstream

| Feature | Upstream | HermesTradingAgents |
|---------|----------|---------------------|
| Default LLM | OpenAI (GPT-5.4) | **DeepSeek** (deepseek-chat) |
| MCP Tool | ❌ | ✅ `mcp/hermes_trading_tool.py` |
| Docker base | python:3.12-slim | Ubuntu 24.04 target (bookworm) |
| Config ready | .env.example | `.env.hermes` préconfiguré |
| Hermes skill | ❌ | ✅ Appelable depuis Telegram |

## Quick Start

### 1. Clone
```bash
git clone https://github.com/AtlasNexusOps/HermesTradingAgents.git
cd HermesTradingAgents
```

### 2. Configure API key
```bash
cp .env.hermes .env
# Éditer .env → coller ta DEEPSEEK_API_KEY
```

### 3. Run with Docker
```bash
# Mode DeepSeek (cloud)
docker compose -f docker-compose.hermes.yml up -d

# Analyse interactive
docker exec -it hermes-trading-agents python main.py
```

### 4. MCP Mode (for Hermes Agent)
```bash
docker run -i --env-file .env hermes-trading-agents python mcp/hermes_trading_tool.py
```

Hermes peut alors appeler l'outil `trading_analyze` avec :
```json
{"ticker": "AAPL", "date": "2026-05-19"}
```

## Architecture

```
┌─────────────────────────────────────┐
│         Hermes Agent (Telegram)      │
│  "Analyse AAPL cette semaine"        │
└──────────────┬──────────────────────┘
               │ MCP JSON-RPC
┌──────────────▼──────────────────────┐
│     mcp/hermes_trading_tool.py       │
│     trading_analyze(ticker, date)    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     TradingAgentsGraph (LangGraph)   │
│  ┌─────────┐  ┌───────────┐         │
│  │Analysts │→│Researchers│         │
│  │(4 types)│  │(bull/bear)│         │
│  └─────────┘  └─────┬─────┘         │
│                     ↓               │
│  ┌─────────┐  ┌───────────┐         │
│  │  Risk   │← │  Trader   │         │
│  │Manager  │  │           │         │
│  └─────────┘  └───────────┘         │
└─────────────────────────────────────┘
```

## Providers supportés

| Provider | Clé API |
|----------|---------|
| **DeepSeek** ⭐ | `DEEPSEEK_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Google Gemini | `GOOGLE_API_KEY` |
| xAI Grok | `XAI_API_KEY` |
| Ollama (local) | Aucune |

## License

MIT — voir [LICENSE](LICENSE)

## Disclaimer

Ce framework est destiné à la **recherche uniquement**. Il ne constitue pas un conseil financier.
Les performances varient selon le modèle, la température et la qualité des données.
