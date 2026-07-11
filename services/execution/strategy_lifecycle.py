"""
Strategy Lifecycle Manager — auto-promotes/demotes strategies from backtest result JSON.
Removes the manual promotion bottleneck by enforcing non-zero evidence + minimal gates.
"""
from __future__ import annotations

import os
import json
import glob
from typing import Any, Dict, List, Optional

from services.shared.logger import get_logger

logger = get_logger("strategy_lifecycle")

RESULTS_DIR = os.getenv("STRATEGY_RESULTS_DIR", os.path.join("data", "rnd", "results"))
REGISTRY_PATH = os.path.join("data", "rnd", "strategy_registry.json")

LIVE_GATES = {
    "min_train_trades": 10,
    "min_train_wr": 0.5,
    "min_full_trades": 20,
    "min_profit_factor": 1.1,
    "max_drawdown_pct": 4.0,
}


def _load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _scan_results() -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for path in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
        data = _load_json(path)
        if not isinstance(data, dict):
            continue
        trades = int(data.get("trades", data.get("total_trades", 0)) or 0)
        if trades <= 0:
            continue
        candidates.append({
            "source_file": os.path.basename(path),
            "strategy_id": data.get("strategy_id", os.path.splitext(os.path.basename(path))[0]),
            "timeframe": data.get("timeframe", ""),
            "symbol": data.get("symbol", "XAUUSD"),
            "train_trades": int(data.get("train_trades", data.get("trades", 0))),
            "train_wr": float(data.get("train_wr", data.get("win_rate", 0.0)) or 0.0),
            "profit_factor": float(data.get("profit_factor", data.get("pf", 0.0)) or 0.0),
            "max_drawdown_pct": float(data.get("max_drawdown_pct", data.get("max_dd", 0.0)) or 0.0),
        })
    return candidates


def _passes(candidate: Dict[str, Any]) -> bool:
    return (
        candidate["train_trades"] >= LIVE_GATES["min_train_trades"]
        and candidate["train_wr"] >= LIVE_GATES["min_train_wr"]
        and candidate["profit_factor"] >= LIVE_GATES["min_profit_factor"]
        and candidate["max_drawdown_pct"] <= LIVE_GATES["max_drawdown_pct"]
    )


def evaluate() -> Dict[str, Any]:
    candidates = _scan_results()
    approved = []
    rejected = []
    for c in candidates:
        if _passes(c):
            c.update({"status": "live_allowed", "decision": "trade_live"})
            approved.append(c)
        else:
            c.update({"status": "research_only", "decision": "do_not_trade_live"})
            rejected.append(c)
    summary = {
        "evaluated": len(candidates),
        "approved": len(approved),
        "rejected": len(rejected),
        "approved_ids": [c["strategy_id"] for c in approved],
    }
    try:
        os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": __import__("time").time(), "approved": approved, "rejected": rejected, "summary": summary}, f, indent=2)
    except Exception as ex:
        logger.warning("Failed to write strategy registry: %s", ex)
    logger.info("Strategy lifecycle evaluated %d; approved %d", len(candidates), len(approved))
    return summary


def approved_strategies() -> List[str]:
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [c["strategy_id"] for c in data.get("approved", []) if c.get("status") == "live_allowed"]
    except Exception:
        return []
