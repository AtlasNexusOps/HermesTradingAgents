#!/usr/bin/env python3
"""
Hermes MCP Trading Tool — Analyse financière multi-agent via LangGraph.

Usage en mode MCP (JSON-RPC sur stdin/stdout) :
  python hermes_trading_tool.py

Endpoint appelable par Hermes :
  tool: trading_analyze
  params: { ticker: str, date?: str, deep_think_llm?: str, quick_think_llm?: str }
"""

import sys
import json
import os
from datetime import date

# Charger .env si présent
def _load_dotenv():
    for p in (".env", ".env.hermes"):
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_dotenv()

# ── MCP JSON-RPC dispatcher ──────────────────────────────────────

def handle_request(req: dict) -> dict:
    method = req.get("method", "")
    req_id = req.get("id")

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "trading_analyze",
                        "description": "Run multi-agent LLM trading analysis on a stock ticker. Returns buy/sell/hold recommendation with analyst reports and debate summary.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "ticker": {
                                    "type": "string",
                                    "description": "Stock ticker symbol (e.g., AAPL, NVDA, TSLA)"
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Analysis date in YYYY-MM-DD format (default: today)"
                                },
                                "deep_think_llm": {
                                    "type": "string",
                                    "description": "Deep-thinking LLM model (default: deepseek-chat)"
                                },
                                "quick_think_llm": {
                                    "type": "string",
                                    "description": "Quick-thinking LLM model (default: deepseek-chat)"
                                }
                            },
                            "required": ["ticker"]
                        }
                    }
                ]
            }
        }

    if method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name == "trading_analyze":
            try:
                result = run_analysis(
                    ticker=arguments["ticker"],
                    analysis_date=arguments.get("date"),
                    deep_think_llm=arguments.get("deep_think_llm"),
                    quick_think_llm=arguments.get("quick_think_llm"),
                )
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": result}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)}
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"}
    }


def run_analysis(
    ticker: str,
    analysis_date: str | None = None,
    deep_think_llm: str | None = None,
    quick_think_llm: str | None = None,
) -> str:
    """Execute a trading analysis and return formatted result."""

    if analysis_date is None:
        analysis_date = date.today().strftime("%Y-%m-%d")

    # Override config via env vars
    os.environ["TRADINGAGENTS_LLM_PROVIDER"] = os.environ.get("TRADINGAGENTS_LLM_PROVIDER", "deepseek")
    if deep_think_llm:
        os.environ["TRADINGAGENTS_DEEP_THINK_LLM"] = deep_think_llm
    if quick_think_llm:
        os.environ["TRADINGAGENTS_QUICK_THINK_LLM"] = quick_think_llm

    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG

    config = DEFAULT_CONFIG.copy()
    config["output_language"] = os.environ.get("TRADINGAGENTS_OUTPUT_LANGUAGE", "English")

    graph = TradingAgentsGraph(debug=False, config=config)
    _, decision = graph.propagate(ticker, analysis_date)

    # Format output
    lines = [
        f"## 📊 Trading Analysis: {ticker} ({analysis_date})",
        "",
        str(decision),
    ]
    return "\n".join(lines)


# ── Main: JSON-RPC loop ──────────────────────────────────────────

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()
