from __future__ import annotations

import json
import os
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MT5_COMMON = Path(r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\Common\Files")
BUS_DIR = REPO / "omni-core" / "agents" / "meta"
AI_CMD_PATH = MT5_COMMON / "AI_Command.json"
VALIDATOR = REPO / "omni-core" / "validators" / "master_validator.py"
LOG_PATH = REPO / "omni-core" / "validators" / "logs" / "bus_monitor.log"
STATE_PATH = REPO / "omni-core" / "validators" / "memory" / "bus_monitor_state.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def list_bus_files():
    if not BUS_DIR.exists():
        return []
    return sorted(BUS_DIR.glob("*.json"))


def extract_price(text: str):
    import re
    m = re.search(r"at\s+([0-9]+(?:\.[0-9]+)?)", str(text))
    if m:
        return float(m.group(1))
    return None


def enqueue_new(q: queue.Queue, seen: set):
    for path in list_bus_files():
        if path.name not in seen:
            data = read_json(path)
            text = data.get("message") or data.get("signal") or ""
            price = extract_price(text)
            q.put({"path": str(path), "message": text, "price": price})
            seen.add(path.name)


def run_cycle(seen: set):
    q: queue.Queue = queue.Queue()
    enqueue_new(q, seen)

    state = read_json(STATE_PATH)
    state["last_run"] = utc_now_iso()

    # Simplified monitor log: execute validator-derived command state as write-through.
    cmd = read_json(AI_CMD_PATH) if AI_CMD_PATH.exists() else {}
    summary = {
        "timestamp": utc_now_iso(),
        "queued_messages": q.qsize(),
        "status": cmd.get("status", "unknown"),
        "direction": cmd.get("direction"),
        "emergency_halt": cmd.get("emergency_halt", False),
        "latest_seen_count": len(seen),
    }
    write_json_atomic(STATE_PATH, state)

    log_line = json.dumps(summary, default=str)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception:
        pass
    print(log_line)


def start(interval_seconds: int = 2):
    BUS_DIR.mkdir(parents=True, exist_ok=True)
    MT5_COMMON.mkdir(parents=True, exist_ok=True)
    seen = set(p.name for p in list_bus_files())
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(STATE_PATH, {"status": "run", "started": utc_now_iso(), "seen_count": len(seen)})
    print(f"{utc_now_iso()} BUS monitor started interval={interval_seconds}s seen={len(seen)}")
    try:
        while True:
            start_ts = time.time()
            run_cycle(seen)
            time.sleep(max(0.0, interval_seconds - (time.time() - start_ts)))
    except KeyboardInterrupt:
        write_json_atomic(STATE_PATH, {"status": "stopped", "stopped": utc_now_iso(), "seen_count": len(seen)})
        print(f"{utc_now_iso()} BUS monitor stopped")


def stop():
    write_json_atomic(STATE_PATH, {"status": "stop_requested", "requested": utc_now_iso()})
    print(json.dumps({"status": "stop_requested", "state_path": str(STATE_PATH)}, indent=2))


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "start":
        start(2)
    elif cmd == "stop":
        stop()
