from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path(os.path.dirname(os.path.abspath(__file__))).parent
SPRINT = REPO / "data" / "sprint"
RESULTS_DIR = REPO / "data" / "rnd" / "results"
TFS = ["M1", "M5", "M15", "H4", "D1", "W1"]
INSTRUMENT = "BTCUSD"
BACKTEST = "http://127.0.0.1:5560"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event: str, payload: dict) -> None:
    row = {"ts": now(), "event": event, **payload}
    path = SPRINT / "lane2.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def backtest_request(strategy_id: str, timeframe: str) -> dict:
    return {
        "strategy_id": strategy_id,
        "name": strategy_id,
        "instrument": INSTRUMENT,
        "timeframe": timeframe,
        "session_filter": ["london", "newyork", "overlap"],
        "entry_logic": {"type": strategy_id, "description": f"lane2_sweep_{strategy_id}"},
        "sl_logic": {"type": "atr", "value": 14, "multiplier": 1.5},
        "tp_logic": {"type": "atr", "value": 28, "multiplier": 3.0},
        "risk_pct": 0.5,
        "max_trades_per_day": 5,
        "spread_gate_pips": 30,
        "date_from": "",
        "date_to": "",
    }


def run_one(strategy_id: str, timeframe: str) -> dict:
    route = f"{BACKTEST}/backtest"
    body = backtest_request(strategy_id, timeframe)
    started = time.time()
    try:
        r = requests.post(route, json=body, timeout=120)
        duration = round(time.time() - started, 3)
        out = {
            "strategy": strategy_id,
            "timeframe": timeframe,
            "instrument": INSTRUMENT,
            "status_code": r.status_code,
            "duration_sec": duration,
            "route": route,
        }
        if r.status_code == 200:
            data = r.json()
            wr = float(data.get("win_rate", 0.0))
            trades = int(data.get("total_trades", 0))
            exp_r = float(data.get("expectancy_r", 0.0))
            mdd = float(data.get("max_drawdown_pct", 0.0))
            pf = float(data.get("profit_factor", 1.0))
            passed = (
                trades >= 50
                and wr >= 0.52
                and exp_r >= 0.40
                and mdd <= 10.0
            )
            out.update(
                {
                    "win_rate": wr,
                    "total_trades": trades,
                    "expectancy_r": exp_r,
                    "max_drawdown_pct": mdd,
                    "profit_factor": pf,
                    "pass": passed,
                }
            )
            return out
        txt = ""
        try:
            txt = r.json().get("detail", r.text)
        except Exception:
            txt = r.text
        out["body"] = txt[:400]
        out["pass"] = False
        return out
    except Exception as e:  # pragma: no cover - runtime only
        return {
            "strategy": strategy_id,
            "timeframe": timeframe,
            "instrument": INSTRUMENT,
            "status_code": None,
            "duration_sec": round(time.time() - started, 3),
            "error": str(e),
            "pass": False,
        }


def run_sweep() -> None:
    log_event("lane2_start", {"message": "cross-timeframe backtest sweep"})
    strategies = [
        "gold_breakout",
        "gold_nbc_pullback",
        "gold_nbc_pullback_v2",
        "fvg_fill",
        "ob_reaction",
        "bos_retest",
        "choch_confirm",
        "ob_fvg_confluent",
        "liquidity_sweep_reversal",
        "killzone_ob_entry",
    ]
    tasks = [(sid, tf) for sid in strategies for tf in TFS]
    log_event("plan", {"tasks": len(tasks), "strategies": strategies, "timeframes": TFS, "instrument": INSTRUMENT})
    started = now()
    results = []
    ok_count = 0
    fail_count = 0
    for idx, (sid, tf) in enumerate(tasks, 1):
        item = run_one(sid, tf)
        results.append(item)
        if item.get("pass"):
            ok_count += 1
        else:
            fail_count += 1
        log_event("task", {"idx": idx, "total": len(tasks), **item})
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"lane2_sweep_{ts_slug}.json"
    summary = {
        "started": started,
        "instrument": INSTRUMENT,
        "total_tasks": len(results),
        "passed": ok_count,
        "failed_or_na": fail_count,
        "results": results,
    }
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log_event(
        "lane2_end",
        {
            "out_path": str(out_path),
            "passed": ok_count,
            "failed_or_na": fail_count,
            "total_tasks": len(results),
        },
    )


def main() -> None:
    run_sweep()


if __name__ == "__main__":
    main()
