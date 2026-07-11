from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MT5_COMMON = Path(r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\Common\Files")
BUS_DIR = REPO / "omni-core" / "agents" / "meta"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    filename = f"signal_{agent_id}_{strategy}_{uuid.uuid4().hex}.json"
    path = MT5_COMMON / filename
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def main():
    paths = [
        write_signal("03", "OB", "BUY", 4185.50),
        write_signal("14", "HarmonicPatterns", "BUY", 4185.70),
        write_signal("07", "TrendLines", "BUY", 4185.40),
    ]
    print("\n".join(str(p) for p in paths))


if __name__ == "__main__":
    main()
