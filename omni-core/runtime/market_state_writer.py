from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MT5_COMMON = Path(r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\Common\Files")
NATIVE_ACCOUNT = "http://localhost:7779/api/native/account"
NATIVE_BARS = "http://localhost:7779/api/native/bars"
SYMBOL = os.getenv("OMNI_SYMBOL", "XAUUSD")
TIMEFRAME = os.getenv("OMNI_TIMEFRAME", "M15")
STATE_FILE = REPO / "omni-core" / "runtime" / "feed_state.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_json(url: str):
    import urllib.request
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def read_market_state_file() -> dict:
    path = MT5_COMMON / "Market_State.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def derive_daily_open_from_native(native_account: dict, symbol: str) -> float:
    try:
        url = f"{NATIVE_BARS}?symbol={symbol}&timeframe=D1&limit=2"
        data = fetch_json(url)
        bars = data.get("bars") if isinstance(data, dict) else None
        if not bars and isinstance(data, list):
            bars = data
        if bars:
            latest = bars[-1]
            return float(latest.get("open") or latest.get("Open") or 0.0)
    except Exception:
        pass
    return 0.0


def build_market_state(native_account: dict, existing_state: dict) -> dict:
    account = native_account if isinstance(native_account, dict) else {}
    equity = float(account.get("equity") or existing_state.get("equity") or 0.0)
    balance = float(account.get("balance") or existing_state.get("balance") or 0.0)
    profit = float(account.get("profit") or existing_state.get("daily_pnl") or 0.0)
    daily_open = float(existing_state.get("daily_open") or 0.0) or derive_daily_open_from_native(account, SYMBOL)

    feed = {
        "symbol": existing_state.get("symbol") or SYMBOL,
        "timeframe": existing_state.get("timeframe") or TIMEFRAME,
        "session": existing_state.get("Session") or existing_state.get("session") or "Unknown",
        "daily_open": daily_open,
        "ask": float(existing_state.get("ask") or 0.0),
        "bid": float(existing_state.get("bid") or 0.0),
        "last_candle_close": float(existing_state.get("last_candle_close") or 0.0),
        "timestamp": utc_now_iso(),
        "source": "omni-core/runtime/market_state_writer",
        "status": "live",
        "daily_pnl": profit,
        "account": {
            "login": account.get("login"),
            "balance": account.get("balance"),
            "equity": account.get("equity"),
            "profit": account.get("profit"),
            "margin_free": account.get("margin_free"),
            "margin_level": account.get("margin_level"),
            "trade_mode": account.get("trade_mode"),
            "trade_allowed": account.get("trade_allowed"),
            "server": account.get("server"),
            "currency": account.get("currency"),
        },
    }
    return feed


def write_json_atomic(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def main():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    MT5_COMMON.mkdir(parents=True, exist_ok=True)

    target_path = MT5_COMMON / "Market_State.json"
    existing_state = read_market_state_file()

    native_account = {}
    try:
        native_account = fetch_json(NATIVE_ACCOUNT)
    except Exception as exc:
        msg = f"native/account fetch failed: {exc}"
        state = {
            "last_run": utc_now_iso(),
            "status": "degraded",
            "error": msg,
        }
        write_json_atomic(STATE_FILE, state)
        print(json.dumps(state, indent=2))
        return

    market_state = build_market_state(native_account, existing_state)
    write_json_atomic(target_path, market_state)
    write_json_atomic(STATE_FILE, {
        "last_written": utc_now_iso(),
        "path": str(target_path),
        "symbol": market_state.get("symbol"),
        "daily_open": market_state.get("daily_open"),
        "ask": market_state.get("ask"),
        "bid": market_state.get("bid"),
        "daily_pnl": market_state.get("daily_pnl"),
    })
    print(json.dumps({"status": "ok", "path": str(target_path), "data": market_state}, indent=2))


if __name__ == "__main__":
    main()
