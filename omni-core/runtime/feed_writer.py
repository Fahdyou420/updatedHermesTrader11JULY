from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MT5_COMMON = Path(r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\Common\Files")
FEED_PATH = MT5_COMMON / "OmniVision_Feed.json"
STATE_FILE = REPO / "omni-core" / "runtime" / "feed_state.json"
NATIVE_ACCOUNT = "http://localhost:7779/api/native/account"
SYMBOL = os.getenv("OMNI_SYMBOL", "XAUUSD")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_json(url: str):
    if url.startswith("http"):
        import urllib.request
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    path = Path(url)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def write_json_atomic(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_account_feed():
    return fetch_json(NATIVE_ACCOUNT)


def read_market_state():
    try:
        return json.loads((MT5_COMMON / "Market_State.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def derive_daily_open_from_history(symbol: str) -> float:
    # Hardcoded current known daily open for XAUUSD; replace with scheduled OHLC fetch.
    return 4186.00


def first_nonzero(value, fallback):
    try:
        value = float(value)
        if value:
            return value
    except Exception:
        pass
    return fallback


def build_runtime_feed(account_feed, market_state):
    daily_open = derive_daily_open_from_history(SYMBOL)
    session = next(
        (
            market_state.get(k)
            for k in ["Session", "session"]
            if market_state.get(k)
        ),
        "Unknown",
    )
    ask = first_nonzero(
        market_state.get("ask") or market_state.get("Ask"), 0.0
    )
    bid = first_nonzero(
        market_state.get("bid") or market_state.get("Bid"), 0.0
    )
    last_candle_close = first_nonzero(
        market_state.get("last_candle_close") or market_state.get("lastClose"), 0.0
    )

    base = {
        "symbol": SYMBOL,
        "timeframe": next(
            (
                market_state.get(k)
                for k in ["Timeframe", "timeframe"]
                if market_state.get(k)
            ),
            "PERIOD_M15",
        ),
        "session": session,
        "daily_open": daily_open,
        "daily_pnl": float(account_feed.get("profit") or 0.0),
        "ask": ask,
        "bid": bid,
        "last_candle_close": last_candle_close,
        "timestamp": utc_now_iso(),
        "source": "OmniVision_Feed",
        "status": "live",
        "strategies": market_state.get("Strategies") or market_state.get("strategies") or {
            "MSS": False,
            "BOS": False,
            "OB": False,
            "FVG": False,
            "Liquidity_Sweep": False,
            "ATR_Expansion": False,
        },
        "indicators": market_state.get("Indicators") or market_state.get("indicators") or {},
        "account": {
            "login": account_feed.get("login"),
            "balance": account_feed.get("balance"),
            "equity": account_feed.get("equity"),
            "profit": account_feed.get("profit"),
            "margin_free": account_feed.get("margin_free"),
            "margin_level": account_feed.get("margin_level"),
            "trade_mode": account_feed.get("trade_mode"),
            "trade_allowed": account_feed.get("trade_allowed"),
            "server": account_feed.get("server"),
            "currency": account_feed.get("currency"),
            "timestamp": utc_now_iso(),
        },
        "meta": {
            "feed_writer": "omni-core/runtime/feed_writer",
            "writing_process": os.getpid(),
            "market_state_mtime": None,
        },
    }
    return base


def main():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    MT5_COMMON.mkdir(parents=True, exist_ok=True)

    account_feed = read_account_feed()
    market_state = read_market_state()
    feed = build_runtime_feed(account_feed, market_state)

    write_json_atomic(FEED_PATH, feed)
    write_json_atomic(STATE_FILE, {
        "last_written": utc_now_iso(),
        "feed_path": str(FEED_PATH),
        "market_state_path": str(MT5_COMMON / "Market_State.json"),
        "symbol": SYMBOL,
        "ask": feed.get("ask"),
        "bid": feed.get("bid"),
        "daily_open": feed.get("daily_open"),
        "account": {
            "balance": account_feed.get("balance"),
            "equity": account_feed.get("equity"),
            "profit": account_feed.get("profit"),
            "trade_allowed": account_feed.get("trade_allowed"),
        },
        "meta": feed.get("meta", {}),
    })
    print(json.dumps({"status": "ok", "feed_path": str(FEED_PATH), "data": feed}, indent=2))


if __name__ == "__main__":
    main()
