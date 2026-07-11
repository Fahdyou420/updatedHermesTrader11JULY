"""
Hermes Layer 4 Execution Engine
================================
Long-running background operator for Windows 11 Git Bash.

Monitors   : C:/Users/user/Desktop/hermes_claude/scripts/live_trader/
              for approved signal files (JSON/JSONL with "status":"approved").
Executes   : via native SEND_NATIVE_ORDER path at http://localhost:7779/mcp
Fleet mgr  : get_open_positions on each tick
Halt       : daily drawdown <= -2000 USD from saved day-start equity
Log        : C:/Users/user/Desktop/hermes_claude/HermesLogs/send_execution.log

Requirements: requests
"""

import json
import os
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("FATAL: requests package is not installed. Run: pip install requests")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
WATCH_DIR = Path(r"C:/Users/user/Desktop/hermes_claude/scripts/live_trader")
LOG_PATH = Path(r"C:/Users/user/Desktop/hermes_claude/HermesLogs/send_execution.log")
STATE_FILE = WATCH_DIR / ".l4_execution_operator.state.json"

WATCH_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
MCP_URL = "http://localhost:7779/mcp"
REST_ACCOUNT_URL = "http://localhost:7779/api/native/account"
REST_POSITIONS_URL = "http://localhost:7779/api/native/positions"

# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------
TICK_SECONDS = 60
MAX_DAILY_DRAWDOWN_USD = -2000.0

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("l4_execution")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(ch)


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------
def _today():
    return datetime.now().strftime("%Y-%m-%d")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if data.get("date") == _today():
                return data
        except Exception:
            pass
    return {
        "date": _today(),
        "day_start_equity": None,
        "halted": False,
        "processed": {},   # filename -> mtime
    }


def save_state(state: dict):
    state["date"] = _today()
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"State save failed: {e}")


# ---------------------------------------------------------------------------
# Account / drawdown
# ---------------------------------------------------------------------------
def ensure_day_start_equity(state: dict) -> float | None:
    if state.get("day_start_equity") is not None:
        return state["day_start_equity"]
    try:
        r = requests.get(REST_ACCOUNT_URL, timeout=5)
        if r.ok:
            equity = float(r.json().get("equity", 0.0))
            state["day_start_equity"] = equity
            state["halted"] = False
            logger.info(f"Day-start equity recorded: {equity:.2f} USD")
            save_state(state)
            return equity
    except Exception as e:
        logger.error(f"Failed to fetch account equity for day-start: {e}")
    return None


def check_drawdown_halt(state: dict) -> bool:
    day_start = ensure_day_start_equity(state)
    if day_start is None:
        return state.get("halted", False)
    try:
        r = requests.get(REST_ACCOUNT_URL, timeout=5)
        if not r.ok:
            return state.get("halted", False)
        current_equity = float(r.json().get("equity", day_start))
        drawdown = current_equity - day_start
        if drawdown <= MAX_DAILY_DRAWDOWN_USD:
            state["halted"] = True
            logger.critical(
                f"HALT | daily_drawdown={drawdown:.2f} USD <= {MAX_DAILY_DRAWDOWN_USD} "
                f"(day_start={day_start:.2f}, current={current_equity:.2f})"
            )
            save_state(state)
            return True
    except Exception as e:
        logger.error(f"Drawdown check failed: {e}")
    return state.get("halted", False)


# ---------------------------------------------------------------------------
# MCP / REST helpers
# ---------------------------------------------------------------------------
def mcp_call(name: str, args: dict | None = None) -> dict:
    """Call localhost:7779/mcp JSON-RPC tools/call."""
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % (2**31),
        "method": "tools/call",
        "params": {"name": name, "arguments": args or {}},
    }
    try:
        r = requests.post(MCP_URL, json=payload, timeout=30)
        if r.ok:
            return r.json()
        return {"error": f"HTTP {r.status_code}", "body": r.text[:300]}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Order placement (safety-first: ALWAYS SL+TP)
# ---------------------------------------------------------------------------
def place_native_order(signal: dict) -> dict:
    direction = str(signal.get("direction", "BUY")).upper()
    symbol = str(signal.get("symbol", "XAUUSD"))
    volume = float(signal.get("volume", 0.01))
    sl = float(signal.get("sl", 0) or 0)
    tp = float(signal.get("tp", 0) or 0)
    comment = str(signal.get("comment", "hermes_l4"))
    entry_price = signal.get("entry_price")

    if not sl or not tp:
        logger.error(f"REJECT | missing_sl_or_tp for signal {signal.get('signal_id')}")
        return {"status": "rejected", "reason": "missing_sl_or_tp"}

    action = direction
    if entry_price is not None:
        action = f"{direction}_LIMIT"

    args = {
        "action": action,
        "symbol": symbol,
        "volume": volume,
        "sl": sl,
        "tp": tp,
        "comment": comment,
    }
    if entry_price is not None:
        args["entry_price"] = float(entry_price)

    logger.info(
        f"SEND_NATIVE_ORDER | action={action} symbol={symbol} volume={volume} "
        f"sl={sl} tp={tp} entry={entry_price}"
    )
    result = mcp_call("send_native_order", args)
    log_extra = json.dumps(result, default=str)[:400]
    logger.info(f"ORDER_RESULT | {log_extra}")
    write_ticket_log(signal, result)
    return result


def write_ticket_log(signal: dict, result: dict):
    """Append ticket + comments/result to send_execution.log."""
    try:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal_id": signal.get("signal_id"),
            "source_file": signal.get("_source_file"),
            "direction": signal.get("direction"),
            "symbol": signal.get("symbol"),
            "volume": signal.get("volume"),
            "sl": signal.get("sl"),
            "tp": signal.get("tp"),
            "result": result,
        }
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as e:
        logger.warning(f"Ticket log write failed: {e}")


# ---------------------------------------------------------------------------
# Fleet management
# ---------------------------------------------------------------------------
def fleet_manage():
    try:
        positions = mcp_call("get_native_positions", {})
        logger.info(f"FLEET | get_open_positions -> {json.dumps(positions, default=str)[:300]}")
    except Exception as e:
        logger.error(f"Fleet management error: {e}")


# ---------------------------------------------------------------------------
# Signal ingestion from watch dir
# ---------------------------------------------------------------------------
def iter_approved_signals(state: dict):
    processed = state.setdefault("processed", {})
    found = []
    try:
        for path in sorted(WATCH_DIR.iterdir()):
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue
            if path.suffix.lower() not in (".json", ".jsonl", ".txt"):
                continue
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            key = f"{path.name}:{mtime:.0f}"
            if processed.get(path.name) == key:
                continue
            signals = _parse_approved(path)
            for sig in signals:
                sig["_source_file"] = path.name
                found.append(sig)
            processed[path.name] = key
    except Exception as e:
        logger.error(f"Directory scan error: {e}")
    return found


def _parse_approved(path: Path) -> list:
    out = []
    try:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return out
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = []
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except Exception:
                    pass
        if isinstance(data, dict):
            data = [data]
        for item in data:
            if isinstance(item, dict) and item.get("status") == "approved":
                out.append(item)
    except Exception as e:
        logger.error(f"Failed to parse {path.name}: {e}")
    return out


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run():
    logger.info("=" * 60)
    logger.info("Hermes Layer 4 Execution Engine starting")
    logger.info(f"Watching : {WATCH_DIR}")
    logger.info(f"Log      : {LOG_PATH}")
    logger.info(f"MCP      : {MCP_URL}")
    logger.info(f"Tick     : {TICK_SECONDS}s")
    logger.info("=" * 60)

    state = load_state()
    try:
        while True:
            if check_drawdown_halt(state):
                logger.critical("Execution halted by daily drawdown limit.")
                break

            approved = iter_approved_signals(state)
            if approved:
                logger.info(f"Dispatched {len(approved)} approved signal(s) for execution")
                for sig in approved:
                    if state.get("halted"):
                        break
                    place_native_order(sig)

            fleet_manage()
            save_state(state)
            time.sleep(TICK_SECONDS)

    except KeyboardInterrupt:
        logger.info("Execution engine stopped by KeyboardInterrupt")
    except Exception as e:
        logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)


if __name__ == "__main__":
    run()
