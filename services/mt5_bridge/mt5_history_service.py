"""Local MT5 history helper for the Hermes MT5 bridge."""
from __future__ import annotations

import os
import sys
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import MetaTrader5 as mt5

    _MT5_AVAILABLE = True
except Exception:  # pragma: no cover
    _MT5_AVAILABLE = False

logger = logging.getLogger("mt5_history_service")

DEFAULT_MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"
DEFAULT_BRIDGE_URL = os.getenv("MT5_BRIDGE_URL", "http://localhost:5558")
LIVE_HISTORY_PATH = Path(os.getenv("LIVE_HISTORY_PATH", "/data/trades/live_history.jsonl"))
FALLBACK_EXPORT_DIRS = [
    Path(r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\Tester\logs"),
    Path(r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs"),
]


class MT5HistoryError(Exception):
    pass


def ensure_mt5_available() -> None:
    if not _MT5_AVAILABLE:
        raise MT5HistoryError("MetaTrader5 Python package is not installed.")


def initialize_terminal(path: Optional[str] = None) -> bool:
    ensure_mt5_available()
    terminal_path = path or os.getenv("MT5_TERMINAL_PATH", DEFAULT_MT5_PATH)
    initialized = mt5.initialize(terminal_path)
    if not initialized:
        raise MT5HistoryError(f"mt5.initialize() failed: {mt5.last_error()}")
    return True


def shutdown_terminal() -> None:
    if _MT5_AVAILABLE:
        try:
            mt5.shutdown()
        except Exception as exc:
            logger.debug("mt5.shutdown() exception: %s", exc)


def parse_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    raise MT5HistoryError("datetime value must be datetime or None")


def history_deals_safe(start: Optional[datetime], end: Optional[datetime]) -> List[Dict[str, Any]]:
    ensure_mt5_available()
    start = parse_datetime(start) or datetime(1970, 1, 1)
    end = parse_datetime(end) or datetime.utcnow()

    initialize_terminal()
    try:
        logger.info("Fetching history_deals_get(%s .. %s)", start.isoformat(), end.isoformat())
        raw_deals = mt5.history_deals_get(start, end)
        if raw_deals is None:
            error = mt5.last_error()
            logger.error("history_deals_get returned None: %s", error)
            return []
        deals: List[Dict[str, Any]] = []
        for raw in raw_deals:
            deals.append(
                {
                    "ticket": int(raw),
                    "order": int(mt5.history_deal_get_integer(raw, mt5.DEAL_ORDER)),
                    "time": int(mt5.history_deal_get_integer(raw, mt5.DEAL_TIME)),
                    "type": int(mt5.history_deal_get_integer(raw, mt5.DEAL_TYPE)),
                    "entry": int(mt5.history_deal_get_integer(raw, mt5.DEAL_ENTRY)),
                    "volume": float(mt5.history_deal_get_double(raw, mt5.DEAL_VOLUME)),
                    "price": float(mt5.history_deal_get_double(raw, mt5.DEAL_PRICE)),
                    "commission": float(mt5.history_deal_get_double(raw, mt5.DEAL_COMMISSION)),
                    "swap": float(mt5.history_deal_get_double(raw, mt5.DEAL_SWAP)),
                    "profit": float(mt5.history_deal_get_double(raw, mt5.DEAL_PROFIT)),
                    "symbol": mt5.history_deal_get_string(raw, mt5.DEAL_SYMBOL) or "",
                    "comment": mt5.history_deal_get_string(raw, mt5.DEAL_COMMENT) or "",
                    "magic": int(mt5.history_deal_get_integer(raw, mt5.DEAL_MAGIC)),
                }
            )
        logger.info("history_deals_get returned %d total deals", len(deals))
        return deals
    finally:
        shutdown_terminal()


def symbol_deals(
    symbol: str = "XAUUSD",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    all_deals = history_deals_safe(start, end)
    symbol = symbol.upper()
    return [deal for deal in all_deals if deal.get("symbol", "").upper() == symbol]


def last_deals_count(symbol: str = "XAUUSD", limit: int = 500) -> List[Dict[str, Any]]:
    initialize_terminal()
    try:
        raw_deals = mt5.history_deals_get(0, 0)
        if not raw_deals:
            return []
        matches = []
        for raw in raw_deals:
            sym = mt5.history_deal_get_string(raw, mt5.DEAL_SYMBOL) or ""
            if sym.upper() == symbol.upper():
                matches.append(
                    {
                        "ticket": int(raw),
                        "time": int(mt5.history_deal_get_integer(raw, mt5.DEAL_TIME)),
                        "type": int(mt5.history_deal_get_integer(raw, mt5.DEAL_TYPE)),
                        "entry": int(mt5.history_deal_get_integer(raw, mt5.DEAL_ENTRY)),
                        "volume": float(mt5.history_deal_get_double(raw, mt5.DEAL_VOLUME)),
                        "price": float(mt5.history_deal_get_double(raw, mt5.DEAL_PRICE)),
                        "profit": float(mt5.history_deal_get_double(raw, mt5.DEAL_PROFIT)),
                        "symbol": sym,
                    }
                )
        matches.sort(key=lambda x: x.get("time", 0), reverse=True)
        return matches[:limit]
    finally:
        shutdown_terminal()


def live_history_from_bridge(n: int = 500, instrument: str = "XAUUSD") -> List[Dict[str, Any]]:
    url = f"{DEFAULT_BRIDGE_URL.rstrip('/')}/live_history"
    params = {"n": max(1, min(n, 2000)), "instrument": instrument}
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            deals = data.get("deals") or data.get("history") or []
            if isinstance(deals, list):
                return deals
        logger.error("Unexpected live history payload: %s", type(data).__name__)
        return []
    except Exception as exc:
        logger.error("Live history fetch failed: %s", exc)
        return []


def export_dir_deals(symbol: str, export_dirs: Optional[List[Path]] = None) -> List[Dict[str, Any]]:
    symbol = symbol.upper()
    dirs = export_dirs or FALLBACK_EXPORT_DIRS
    deals: List[Dict[str, Any]] = []
    for directory in dirs:
        if not directory.exists():
            continue
        for path in directory.glob("*.log"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if symbol in text:
                    deals.append({"source": str(path), "raw": text[:200]})
            except Exception as exc:
                logger.debug("log scan failed for %s: %s", path, exc)
    return deals


def diagnose_history(
    symbol: str = "XAUUSD",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Dict[str, Any]:
    if not _MT5_AVAILABLE:
        return {"mt5_api_available": False, "error": "MetaTrader5 package missing"}
    initialize_terminal()
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        history_count = None
        try:
            deals = mt5.history_deals_get(start or datetime(1970, 1, 1), end or datetime.utcnow()) or []
            history_count = len(deals)
        except Exception as exc:  # pragma: no cover - MT5 wrapper edge case
            logger.debug("history_deals_get probe failed: %s", exc)
            history_count = 0
        symbols = [s.name for s in (mt5.symbols_get(symbol) or [])]
        return {
            "mt5_api_available": True,
            "terminal_connected": bool(terminal and terminal.connected),
            "account_login": int(account.login) if account else None,
            "account_server": account.server if account else None,
            "history_count": history_count,
            "symbol_matches": symbols,
            "bridge_live_history_count": len(live_history_from_bridge(instrument=symbol)),
        }
    finally:
        shutdown_terminal()
