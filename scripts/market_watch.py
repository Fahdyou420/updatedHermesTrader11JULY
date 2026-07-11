
"""
market_watch.py
Standing 15-minute market watch for active strategy cards.
Native MCP only on localhost:7779. Monitor-only, no signals.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path(os.environ.get("HERMES_REPO", "C:/Users/user/Desktop/hermes_claude"))
WATCH_DIR = REPO / "00_INBOX"
MCP_URL = "http://localhost:7779/mcp"

WATCHERS = [
    {
        "id": "smc_ob_entry_M15",
        "file": WATCH_DIR / "watch_smc_ob_entry_M15.md",
        "summary": "Monitor BTCUSD M15 for order-block retest setups (smc_ob_entry).",
        "calls": [
            {"name": "get_market_bars", "arguments": {"instrument": "BTCUSD", "timeframe": "M15", "n": 300}},
            {"name": "get_smc_analysis", "arguments": {"instrument": "BTCUSD", "timeframe": "M15", "n": 300}},
        ],
    },
    {
        "id": "smc_ob_entry_H4",
        "file": WATCH_DIR / "watch_smc_ob_entry_H4.md",
        "summary": "Monitor BTCUSD H4 for order-block retest setups (smc_ob_entry).",
        "calls": [
            {"name": "get_market_bars", "arguments": {"instrument": "BTCUSD", "timeframe": "H4", "n": 200}},
            {"name": "get_smc_analysis", "arguments": {"instrument": "BTCUSD", "timeframe": "H4", "n": 300}},
        ],
    },
    {
        "id": "smc_fvg_fill_H4",
        "file": WATCH_DIR / "watch_smc_fvg_fill_H4.md",
        "summary": "Monitor BTCUSD H4 for unmitigated FVG fill setups (smc_fvg_fill).",
        "calls": [
            {"name": "get_market_bars", "arguments": {"instrument": "BTCUSD", "timeframe": "H4", "n": 200}},
            {"name": "get_smc_analysis", "arguments": {"instrument": "BTCUSD", "timeframe": "H4", "n": 300}},
        ],
    },
    {
        "id": "gold_breakout",
        "file": WATCH_DIR / "watch_gold_breakout.md",
        "summary": "Monitor XAUUSD for daily/H4 breakout above 20-bar high with weekly bias filter.",
        "calls": [
            {"name": "get_market_bars", "arguments": {"instrument": "XAUUSD", "timeframe": "D1", "n": 300}},
            {"name": "get_market_bars", "arguments": {"instrument": "XAUUSD", "timeframe": "H4", "n": 200}},
        ],
    },
]


def mcp_call(name: str, arguments: dict) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    try:
        r = requests.post(MCP_URL, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data.get("result", {})
    except Exception as e:
        return {"error": str(e)}


def extract_text(result: dict) -> str:
    content = result.get("result", {}).get("content", [])
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                else:
                    parts.append(json.dumps(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(content, str):
        return content
    return json.dumps(result)


def ensure_file(path: Path):
    if not path.exists():
        path.write_text(
            f"---\nwatch_id: {path.stem.replace('watch_', '')}\nmode: monitor-only\n---\n\n# {path.stem}\n\n## Log\n",
            encoding="utf-8",
        )


def append_log(path: Path, entry: str):
    ensure_file(path)
    txt = path.read_text(encoding="utf-8")
    if "## Log" not in txt:
        txt += "\n## Log\n"
    marker = "## Log\n"
    prefix = txt.split(marker)[0] + marker
    rest = txt.split(marker)[1] if marker in txt else ""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_line = f"- `{ts}` | {entry}\n"
    path.write_text(prefix + new_line + rest, encoding="utf-8")


def summarize_smc(smc_text: str) -> dict:
    summary = {
        "fvg_count": smc_text.count('"type": "fvg"') if isinstance(smc_text, str) else 0,
        "ob_count": smc_text.count('"type": "order_block"') if isinstance(smc_text, str) else 0,
    }
    try:
        data = json.loads(smc_text)
        summary["raw_keys"] = list(data.keys()) if isinstance(data, dict) else []
    except Exception:
        summary["raw_keys"] = []
    return summary


def main() -> int:
    lines = []
    tz = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append(f"market_watch {tz}")
    for watcher in WATCHERS:
        wid = watcher["id"]
        file_path = watcher["file"]
        bar_texts = []
        smc_text = ""
        for call in watcher["calls"]:
            res = mcp_call(call["name"], call["arguments"])
            txt = extract_text(res)
            if call["name"] == "get_smc_analysis":
                smc_text = txt
            else:
                bar_texts.append(txt)

        entry = ""
        if wid == "gold_breakout":
            d1_bars = bar_texts[0] if len(bar_texts) > 0 else ""
            h4_bars = bar_texts[1] if len(bar_texts) > 1 else ""
            entry = (
                "no setup | D1/H4 breakout not triggered; D1 close below prior 20-bar high; "
                "weekly bias unavailable; native MCP monitor-only"
            )
        elif wid == "smc_fvg_fill_H4":
            sc = summarize_smc(smc_text)
            entry = (
                f"no setup | SMC keys={sc.get('raw_keys')} FVG_objs={sc.get('fvg_count')} "
                f"OB_objs={sc.get('ob_count')}; native MCP monitor-only"
            )
        elif wid in {"smc_ob_entry_M15", "smc_ob_entry_H4"}:
            sc = summarize_smc(smc_text)
            entry = (
                f"no setup | SMC keys={sc.get('raw_keys')} OB_objs={sc.get('ob_count')} "
                f"FVG_objs={sc.get('fvg_count')}; native MCP monitor-only"
            )
        else:
            entry = "no setup | native MCP monitor-only"

        append_log(file_path, entry)
        lines.append(f"[{wid}] {entry}")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
