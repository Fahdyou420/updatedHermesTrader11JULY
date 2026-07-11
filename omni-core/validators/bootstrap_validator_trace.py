from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MT5_COMMON = Path(r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\Common\Files")
BUS_DIR = REPO / "omni-core" / "agents" / "meta"
STATE_FILE = REPO / "omni-core" / "runtime" / "feed_state.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def write_signal(agent_id: str, strategy: str, direction: str, price: float, timeframe: str = "M15", symbol: str = "XAUUSD") -> Path:
    message = f"[SIGNAL] Agent {agent_id} ({strategy}): Valid demand zone identified at {price:.2f}." if direction == "BUY" else f"[SIGNAL] Agent {agent_id} ({strategy}): Valid supply zone identified at {price:.2f}."
    payload = {
        "type": "signal",
        "timestamp": utc_now_iso(),
        "agent_id": agent_id,
        "strategy": strategy,
        "symbol": symbol,
        "timeframe": timeframe,
        "direction": direction,
        "price": float(price),
        "message": message,
    }
    BUS_DIR.mkdir(parents=True, exist_ok=True)
    MT5_COMMON.mkdir(parents=True, exist_ok=True)
    path = MT5_COMMON / f"signal_{agent_id}_{strategy}_{int(datetime.now(timezone.utc).timestamp()*1000)}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def build_demo_signals():
    base = float(os.environ.get("OMNI_SEED", "4185"))
    return [
        {"agent_id": "03", "strategy": "OB", "direction": "BUY", "price": base},
        {"agent_id": "14", "strategy": "HarmonicPatterns", "direction": "BUY", "price": base + 0.40},
        {"agent_id": "07", "strategy": "TrendLines", "direction": "BUY", "price": base - 0.10},
    ]


def run_validator():
    script = REPO / "omni-core" / "validators" / "master_validator.py"
    result = subprocess.run(["python", str(script)], capture_output=True, text=True)
    return result


def append_log(path: Path, record: dict):
    try:
        existing = []
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = [existing]
    except Exception:
        existing = []
    existing.append(record)
    write_json_atomic(path, existing)


def main():
    print(f"{utc_now_iso()} OmniVision bootstrap starting")
    if not STATE_FILE.exists():
        print("Prerequisite: market_state_writer must run first; bootstrap stopping.")
        return

    signal_paths = [write_signal(**item) for item in build_demo_signals()]
    print(f"Signals written={len(signal_paths)}")
    for p in signal_paths:
        print(f"- {p}")

    validator = run_validator()
    print("Validator stdout:\n" + validator.stdout)
    if validator.stderr:
        print("Validator stderr:\n" + validator.stderr)

    ai_command = MT5_COMMON / "AI_Command.json"
    ai_data = {}
    if ai_command.exists():
        try:
            ai_data = json.loads(ai_command.read_text(encoding="utf-8"))
        except Exception:
            ai_data = {}

    trace_path = REPO / "omni-core" / "validators" / "logs" / "bootstrap_trace.json"
    append_log(trace_path, {
        "timestamp": utc_now_iso(),
        "wrote_signals": len(signal_paths),
        "validator_status": ai_data.get("status"),
        "validator_direction": ai_data.get("direction"),
        "price_cluster": ai_data.get("price_cluster"),
        "confluence_count": ai_data.get("confluence_count"),
        "emergency_halt": ai_data.get("emergency_halt"),
        "amd_pass": ai_data.get("amd_pass"),
    })
    print(f"Bootstrap trace written to {trace_path}")
    print(json.dumps(ai_data, indent=2))


if __name__ == "__main__":
    main()
