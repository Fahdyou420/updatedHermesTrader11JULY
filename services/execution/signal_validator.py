"""
Signal Validator — deterministic 11-gate pre-trade filter.
Used by paper trader and execution operator before any order is sent.
"""
from __future__ import annotations

import os
import time
import requests
from typing import Any, Dict, List, Tuple

from services.shared.logger import get_logger

logger = get_logger("signal_validator")

DEFAULT_BRIDGE_URL = os.getenv("MT5_BRIDGE_URL", "http://localhost:5558")
DEFAULT_NATIVE_URL = os.getenv("NATIVE_MT5_URL", "http://localhost:7779")


def _get_bar(instrument: str, timeframe: str = "M15", n: int = 1) -> Dict[str, Any] | None:
    for base in (DEFAULT_BRIDGE_URL, DEFAULT_NATIVE_URL):
        try:
            r = requests.get(
                f"{base}/latest_bars?instrument={instrument}&tf={timeframe}&n={n}",
                timeout=3,
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    return data[-1]
        except Exception:
            continue
    return None


def validate(signal: Any, account_state: Dict[str, Any], open_positions: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Returns (approved, rejection_reason)."""
    instrument = str(getattr(signal, "instrument", signal.get("instrument", "") if isinstance(signal, dict) else ""))
    direction = str(getattr(signal, "direction", signal.get("direction", "") if isinstance(signal, dict) else "")).lower()
    entry_price = float(getattr(signal, "entry_price", signal.get("entry_price", 0.0) if isinstance(signal, dict) else 0.0))
    sl = float(getattr(signal, "sl", signal.get("sl", 0.0) if isinstance(signal, dict) else 0.0))
    tp = float(getattr(signal, "tp", signal.get("tp", 0.0) if isinstance(signal, dict) else 0.0))
    lots = float(getattr(signal, "lots", signal.get("lots", 0.0) if isinstance(signal, dict) else 0.0))
    timeframe = str(getattr(signal, "timeframe", signal.get("timeframe", "M15") if isinstance(signal, dict) else "M15"))
    setup_type = str(getattr(signal, "setup_type", signal.get("setup_type", "") if isinstance(signal, dict) else ""))
    strategy_id = str(getattr(signal, "strategy_id", signal.get("strategy_id", "") if isinstance(signal, dict) else ""))
    confidence = str(getattr(signal, "confidence", signal.get("confidence", "medium") if isinstance(signal, dict) else "medium")).lower()
    mode = str(getattr(signal, "mode", signal.get("mode", "paper") if isinstance(signal, dict) else "paper")).lower()

    # Gate 1: instrument non-empty
    if not instrument:
        return False, "Gate 1: missing instrument"

    # Gate 2: direction valid
    if direction not in ("buy", "sell", "long", "short"):
        return False, f"Gate 2: invalid direction '{direction}'"

    # Gate 3: entry_price > 0
    if entry_price <= 0:
        return False, "Gate 3: entry_price must be > 0"

    # Gate 4: SL must be set and non-zero
    if sl <= 0:
        return False, "Gate 4: SL must be > 0"

    # Gate 5: TP must be set and non-zero
    if tp <= 0:
        return False, "Gate 5: TP must be > 0"

    # Gate 6: SL/TP logic consistent with direction
    if direction in ("buy", "long"):
        if not (sl < entry_price < tp):
            return False, "Gate 6: SL < entry < TP required for long"
    else:
        if not (tp < entry_price < sl):
            return False, "Gate 6: TP < entry < SL required for short"

    # Gate 7: R:R >= 1.0 (paper) / >= 1.5 (live)
    risk = abs(entry_price - sl)
    reward = abs(tp - entry_price)
    if risk <= 0:
        return False, "Gate 7: risk distance is zero"
    rr = reward / risk
    min_rr = 1.5 if mode == "live" else 1.0
    if rr < min_rr:
        return False, f"Gate 7: R:R {rr:.2f} below {min_rr}R minimum for {mode}"

    # Gate 8: lot size sanity
    if lots <= 0:
        return False, "Gate 8: lots must be > 0"

    # Gate 9: confidence not low on live
    if mode == "live" and confidence == "low":
        return False, "Gate 9: low confidence rejected on live mode"

    # Gate 10: strategy_id / setup_type present
    if not strategy_id and not setup_type:
        return False, "Gate 10: strategy_id or setup_type required"

    # Gate 11: max open positions <= 3
    if len(open_positions) >= 3:
        return False, f"Gate 11: already {len(open_positions)}/3 open positions"

    logger.info("Signal passed all 11 gates", extra={"instrument": instrument, "rr": round(rr, 2), "mode": mode})
    return True, "approved"
