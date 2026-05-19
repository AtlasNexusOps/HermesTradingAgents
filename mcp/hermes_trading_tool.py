#!/usr/bin/env python3
"""
Hermes MCP Trading Tool — Analyse financière multi-agent via LangGraph.

Tools: trading_analyze (deep single ticker), market_scan (batch multi-tickers)
"""

import sys, json, os
from datetime import date

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

TOOLS = [
    {
        "name": "trading_analyze",
        "description": "Deep multi-agent analysis of a single stock ticker. 4 analysts + debate + risk review.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker (AAPL, NVDA…)"},
                "date": {"type": "string", "description": "Date YYYY-MM-DD (default: today)"},
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "market_scan",
        "description": "Quick batch scan of multiple tickers. Price, daily change %, volume, and an LLM-generated one-line signal per ticker. Returns ranked overview. Use for 'analyse le marché' or sector overview.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Ticker list (e.g., ['AAPL','NVDA','MSFT','TSLA','META','GOOGL'])"
                },
                "date": {"type": "string", "description": "Date YYYY-MM-DD (default: today)"},
            },
            "required": ["tickers"]
        }
    },
]


def handle_request(req: dict) -> dict:
    method = req.get("method", "")
    req_id = req.get("id")

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        p = req.get("params", {})
        name = p.get("name", "")
        args = p.get("arguments", {})

        try:
            if name == "trading_analyze":
                r = run_analysis(args["ticker"], args.get("date"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": r}]}}
            if name == "market_scan":
                r = run_market_scan(args["tickers"], args.get("date"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": r}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(e)}}

        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {name}"}}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


# ── Deep single-ticker ────────────────────────────────────────────

def run_analysis(ticker: str, analysis_date: str | None = None) -> str:
    if analysis_date is None:
        analysis_date = date.today().strftime("%Y-%m-%d")

    os.environ["TRADINGAGENTS_LLM_PROVIDER"] = os.environ.get("TRADINGAGENTS_LLM_PROVIDER", "deepseek")

    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG

    config = DEFAULT_CONFIG.copy()
    config["output_language"] = "English"
    config["max_debate_rounds"] = 1
    config["max_risk_discuss_rounds"] = 1

    graph = TradingAgentsGraph(debug=False, config=config)
    _, decision = graph.propagate(ticker, analysis_date)

    return f"## 📊 Trading Analysis: {ticker} ({analysis_date})\n\n{decision}"


# ── Market scan (batch) ───────────────────────────────────────────

def run_market_scan(tickers: list[str], analysis_date: str | None = None) -> str:
    if analysis_date is None:
        analysis_date = date.today().strftime("%Y-%m-%d")

    import yfinance as yf
    from openai import OpenAI

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return "❌ DEEPSEEK_API_KEY not set in environment"
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    lines = [f"## 🌐 Market Scan — {analysis_date}\n"]
    green, red = 0, 0

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="5d")
            if hist.empty:
                lines.append(f"### ❌ {t} — no data\n")
                continue

            current = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist) >= 2 else current
            change_pct = ((current - prev) / prev) * 100 if prev else 0
            vol = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0

            if change_pct >= 0:
                green += 1
                arrow = "🟢"
            else:
                red += 1
                arrow = "🔴"

            # Quick LLM signal
            try:
                resp = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{
                        "role": "user",
                        "content": (
                            f"Stock: {t} — Price: ${current:.2f} — "
                            f"Daily change: {change_pct:+.2f}% — Volume: {vol:,}\n"
                            f"Date: {analysis_date}\n\n"
                            f"Based on the price action and volume, give a ONE-LINE trading signal:\n"
                            f"Format exactly: SIGNAL: BUY|SELL|HOLD | REASON: <one short reason>"
                        )
                    }],
                    max_tokens=80,
                    temperature=0.3,
                )
                signal = (resp.choices[0].message.content or "").strip()
            except Exception:
                signal = "SIGNAL: HOLD | REASON: analysis unavailable"

            lines.append(f"### {arrow} {t} — ${current:.2f} ({change_pct:+.2f}%) | Vol: {vol:,}")
            lines.append(f"> {signal}\n")

        except Exception as e:
            lines.append(f"### ❌ {t} — error: {e}\n")

    lines.append("---")
    lines.append(f"**{len(tickers)} tickers** | 🟢 {green} up | 🔴 {red} down")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────

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
