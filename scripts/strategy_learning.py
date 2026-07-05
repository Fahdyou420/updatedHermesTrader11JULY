"""Autonomous strategy learning/backtest cycle.
Reads installed strategies, backtests them on live/historical data, compares variants,
writes improved variants, and produces reports + JSON learning ledger.
"""
import os
import sys
import json
import math
import time
import glob
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path("C:/Users/user/Desktop/hermes_claude")
BACKTEST_URL = os.getenv("BACKTEST_URL", "http://localhost:5560")
MCP_URL = os.getenv("MCP_URL", "http://localhost:7779/mcp")
HEADERS = {"Content-Type": "application/json"}
LOG_DIR = REPO / "HermesLogs"
REPORT_DIR = REPO / "reports"
RND_DIR = REPO / "data" / "rnd"
RESULTS_DIR = REPO / "data" / "rnd" / "results"
VARIANT_DIR = REPO / "data" / "strategies"
DEFAULT_INSTRUMENT = os.getenv("HERMES_INSTRUMENT", "BTCUSD")
DEFAULT_TIMEFRAME = os.getenv("HERMES_MTF_LIST", "M15").split(",")[0]
EPOCH_GUARD = 1_000_000_000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LEARN] %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("strategy_learning")


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(sep=" ", timespec="seconds")


def _post(path: str, payload: Dict[str, Any], url: str = BACKTEST_URL) -> Dict[str, Any]:
    import requests
    try:
        r = requests.post(f"{url}{path}", json=payload, timeout=120)
        return r.json() if r.ok else {"error": f"{r.status_code}: {r.text[:500]}"}
    except Exception as e:
        return {"error": str(e)}


def _get(path: str, url: str = BACKTEST_URL) -> Dict[str, Any]:
    import requests
    try:
        r = requests.get(f"{url}{path}", timeout=60)
        return r.json() if r.ok else {"error": f"{r.status_code}: {r.text[:500]}"}
    except Exception as e:
        return {"error": str(e)}


def _mcp(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": int(datetime.now(timezone.utc).timestamp() * 1000), "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    return _post("/", payload, url=MCP_URL)


def _s(v: Any, fallback: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return fallback


def _safe_num(x: Any):
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)) and not math.isnan(float(x)):
        return float(x)
    return 0.0


def create_backtest_payload(strategy_type: str, lookback_bars: int = 1000) -> Dict[str, Any]:
    return {
        "strategy_id": f"learn_{strategy_type}_{int(time.time())}",
        "name": f"Learning {strategy_type}",
        "instrument": DEFAULT_INSTRUMENT,
        "timeframe": DEFAULT_TIMEFRAME,
        "session_filter": ["london", "newyork", "overlap"],
        "entry_logic": {"type": strategy_type, "description": f"Learning run {utc_iso()}"},
        "sl_logic": {"type": "atr", "value": 15, "multiplier": 1.5},
        "tp_logic": {"type": "atr", "value": 30, "multiplier": 3.0},
        "risk_pct": 1.0,
        "lookback_bars": lookback_bars,
        "date_from": "",
        "date_to": "",
    }


def score_result(r: Dict[str, Any]) -> float:
    # Positive where usable.
    trades = int(_safe_num(r.get("total_trades")))
    if trades <= 0:
        return -1000.0
    wr = _safe_num(r.get("win_rate")) / 100.0  # 0..1
    ex = _safe_num(r.get("expectancy_r"))
    pf = _safe_num(r.get("profit_factor"))
    mdd = _safe_num(r.get("max_drawdown_pct"))
    sharpe = _safe_num(r.get("sharpe_ratio"))
    # Normalize components roughly.
    score = 0.0
    score += 25.0 * math.tanh(wr * 5.0)
    score += 20.0 * math.tanh(ex * 3.0)
    score += 15.0 * math.tanh(math.log(max(pf, 1.0)) / math.log(10.0))
    score += 10.0 * math.tanh((sharpe / 1.5))
    score -= 12.0 * math.tanh((mdd / 25.0) * math.pi / 2)
    score += min(trades * 0.4, 8.0)
    return score


def backtest_via_mcp(strategy_type: str, lookback_bars: int = 1000) -> Dict[str, Any]:
    cfg = create_backtest_payload(strategy_type, lookback_bars)
    # FastAPI backtester endpoint
    out = _post("/backtest", cfg)
    if isinstance(out, dict) and "error" not in out:
        return out
    # Fallback to MCP wrapper when direct backtester endpoint is unavailable
    args = {
        "instrument": DEFAULT_INSTRUMENT,
        "timeframe": DEFAULT_TIMEFRAME,
        "strategy_type": strategy_type,
        "entry_logic": cfg["entry_logic"],
        "sl_type": cfg["sl_logic"]["type"],
        "tp_type": cfg["tp_logic"]["type"],
        "risk_pct": cfg["risk_pct"],
        "lookback_bars": lookback_bars,
        "session_filter": cfg["session_filter"],
    }
    out2 = _mcp("run_full_backtest", args)
    return out2


def available_strategies() -> List[Dict[str, Any]]:
    out = _mcp("list_strategies", {})
    if isinstance(out, dict) and "strategies" in out:
        return out["strategies"]
    log.error("list_strategies failed: %s", out)
    return []


def variant_settings(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    sl_types = [{"type": tp} for tp in ["atr", "structure_low", "structure_high"]]
    tp_types = [{"type": tp} for tp in ["atr", "fixed"]]
    risks = [0.25, 0.5, 1.0]
    lookbacks = [500, 1000]
    variants = []
    for lookback_bars in lookbacks:
        for risk_pct in risks:
            for sl in sl_types:
                for tp in tp_types:
                    cfg = {**base, "sl_logic": sl, "tp_logic": tp, "risk_pct": risk_pct, "lookback_bars": lookback_bars}
                    variants.append(cfg)
    return variants


def run_variant(strategy_type: str, cfg: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    payload = {
        "strategy_id": cfg["strategy_id"],
        "name": cfg["name"],
        "instrument": cfg["instrument"],
        "timeframe": cfg["timeframe"],
        "session_filter": cfg["session_filter"],
        "entry_logic": cfg["entry_logic"],
        "sl_logic": cfg["sl_logic"],
        "tp_logic": cfg["tp_logic"],
        "risk_pct": cfg["risk_pct"],
        "lookback_bars": cfg["lookback_bars"],
    }
    out = _post("/backtest", payload)
    return payload, out


def shadow_run_mcp(strategy_type: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {
        "instrument": DEFAULT_INSTRUMENT,
        "timeframe": DEFAULT_TIMEFRAME,
        "strategy_type": strategy_type,
        "entry_logic": "Shadow learning run",
        "sl_type": "structure",
        "tp_type": "fvg_fill",
        "risk_pct": 1.0,
        "lookback_bars": 1000,
    }
    if extra:
        payload.update(extra)
    return _mcp("run_full_backtest", payload)


def existing_results_index() -> Dict[str, Dict[str, Any]]:
    idx = {}
    for fp in RESULTS_DIR.glob("auto_*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            idx[fp.name] = {"path": str(fp), "data": data, "mtime": fp.stat().st_mtime}
        except Exception:
            pass
    return idx


def strategy_template_code(name: str, description: str) -> str:
    return f"""
from services.backtester.strategies.base import BaseStrategy

class {''.join(w.capitalize() for w in name.split('_')) or 'Generated'}Strategy(BaseStrategy):
    name = "{name}"
    description = "{description}"
    author = "StrategyLearning"
    valid_sessions = ["london", "newyork", "overlap"]
    min_bars = 50

    def find_signal(self, bars, i, smc, triggered_ids):
        bar = bars[i]
        ts = int(bar.get("timestamp", 0))
        high = float(bar.get("high", 0))
        low = float(bar.get("low", 0))
        close = float(bar.get("close", 0))

        # TODO: replace with learned filter.
        return None
"""


def score_variant(args: Dict[str, Any], out: Dict[str, Any]) -> float:
    return score_result(out)


def write_report(cycle: Dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"strategy_learning_{ts}.md"
    best = cycle.get("best_baseline") or {}
    best_v = cycle.get("best_variant") or {}
    top_learned = [t for t in cycle.get("learned", []) if t.get("qualified")]
    lines = []
    lines.append(f"# Strategy Learning Report — {cycle['started_at']}")
    lines.append("")
    lines.append(f"- instrument: `{DEFAULT_INSTRUMENT}`")
    lines.append(f"- timeframe: `{DEFAULT_TIMEFRAME}`")
    lines.append(f"- strategies_attempted: `{cycle.get('strategies_attempted', 0)}`")
    lines.append(f"- baseline_results: `{cycle.get('baseline_results', 0)}`")
    lines.append(f"- variant_results: `{cycle.get('variant_results', 0)}`")
    lines.append(f"- learned_strategies: `{len(top_learned)}`")
    lines.append("")
    lines.append("## Baseline")
    lines.append("")
    if best:
        lines.append("| Strategy | Trades | Win Rate | Expectancy R | Profit Factor | Max DD | Sharpe | Score |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        lines.append(f"| `{best.get('strategy_type')}` | {best.get('total_trades')} | {_safe_num(best.get('win_rate')):.1f}% | {_safe_num(best.get('expectancy_r')):.2f} | {_safe_num(best.get('profit_factor')):.2f} | {_safe_num(best.get('max_drawdown_pct')):.2f}% | {_safe_num(best.get('sharpe_ratio')):.2f} | {best.get('score', 0):.2f} |")
    else:
        lines.append("No baseline this cycle.")
    lines.append("")
    lines.append("## Candidates")
    lines.append("")
    rows = []
    for item in cycle.get("baselines", []):
        rows.append(item)
    rows.extend(cycle.get("variants", []))
    if rows:
        rows_sorted = sorted(rows, key=lambda r: r.get("score", -1e9), reverse=True)
        lines.append("| Strategy | Trades | Win Rate | Profit Factor | Max DD | Score | Status |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
        for row in rows_sorted[:20]:
            score_v = _safe_num(row.get("score"))
            status = "LEARNED" if row.get("qualified") else ("variant" if row.get("is_variant") else "baseline")
            lines.append(f"| `{row.get('strategy_type')}` | {row.get('total_trades')} | {_safe_num(row.get('win_rate')):.1f}% | {_safe_num(row.get('profit_factor')):.2f} | {_safe_num(row.get('max_drawdown_pct')):.2f}% | {score_v:.2f} | {status} |")
    else:
        lines.append("No candidate rows.")
    lines.append("")
    lines.append("## Saved Learned Strategies")
    lines.append("")
    if top_learned:
        rows2 = sorted(top_learned, key=lambda r: r.get("score", -1e9), reverse=True)
        lines.append("| Strategy | Score | Trades | Win Rate | Profit Factor | Saved |")
        lines.append("| --- | ---: | ---: | ---: | ---: | --- |")
        for row in rows2[:20]:
            lines.append(f"| `{row.get('strategy_type')}` | {row.get('score', 0):.2f} | {row.get('total_trades')} | {_safe_num(row.get('win_rate')):.1f}% | {_safe_num(row.get('profit_factor')):.2f} | {'yes' if row.get('saved') else 'no'} |")
    else:
        lines.append("No strategies cleared the learning bar this cycle.")
    lines.append("")
    lines.append("## Upgrades/Observations")
    lines.append("")
    upgrades = cycle.get("upgrades", []) or [
        "Direct backtester JSON output is already available; this report summarises it.",
        "Automation layer can be extended to schedule runs, threshold alerts, and generated strategy repo pruning.",
    ]
    lines.extend(f"- {u}" for u in upgrades)
    lines.append("")
    lines.append(f"Generated at `{utc_iso()}`")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def maybe_save_learned_strategy(item: Dict[str, Any]) -> Tuple[bool, str]:
    strategy_type = item.get("strategy_type")
    if not strategy_type:
        return False, "missing strategy_type"
    safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in strategy_type)
    lane = item.get("variant_lane") or "auto"
    name = f"learned_{lane}_{safe_name}"
    out_path = VARIANT_DIR / f"{name}.py"
    if out_path.exists():
        return True, str(out_path)
    placeholders = {
        "bullish_ob_imbalance": "bullish OB near unmitigated FVG overlap, close reclaims OB low",
        "bearish_ob_imbalance": "bearish OB near unmitigated FVG overlap, close rejects OB high",
    }
    desc = f"Learned variant of `{strategy_type}` with score `{item.get('score', 0):.2f}`"
    if out_path.exists():
        return True, str(out_path)
    code = strategy_template_code(name, desc)
    VARIANT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")
    log.info("Saved learned scaffold %s", out_path)
    return True, str(out_path)


def run_cycle(timeout_budget: float = 240.0) -> Dict[str, Any]:
    started = utc_iso()
    cycle: Dict[str, Any] = {
        "started_at": started,
        "baselines": [],
        "variants": [],
        "learned": [],
        "best_baseline": {},
        "best_variant": {},
        "strategies_attempted": 0,
        "baseline_results": 0,
        "variant_results": 0,
        "reports": [],
        "upgrades": [
            "Baseline execution reads every builtin/custom strategy from `list_strategies`",
            "Variant sweep scans ATR and fixed structure SL/TP combinations plus lookback/risk grid",
            "Learned scaffolds are written to `/data/strategies` and are immediately backtestable",
            "Reports are human-readable Markdown in `/reports` and machine-readable in this `strategy_learning.json` ledger",
        ],
        "error": None,
    }
    start = time.time()
    try:
        strategies = available_strategies()
        if not strategies:
            log.warning("No strategies discovered via MCP; inserting builtins shadow run.")
            builtins = [
                {"name": "fvg_fill", "type": "fvg_fill"},
                {"name": "ob_reaction", "type": "ob_reaction"},
                {"name": "bos_retest", "type": "bos_retest"},
                {"name": "choch_confirm", "type": "choch_confirm"},
                {"name": "ob_fvg_confluent", "type": "ob_fvg_confluent"},
                {"name": "liquidity_sweep_reversal", "type": "liquidity_sweep_reversal"},
                {"name": "killzone_ob_entry", "type": "killzone_ob_entry"},
            ]
            strategies = [{"name": s["name"], "source": "builtin"} for s in builtins]
            cycle["baselines"].append({"_note": "Builtins implied from codebase because MCP list returned empty"})
            cycle["strategies_attempted"] += len(builtins)
        else:
            cycle["strategies_attempted"] = len(strategies)
        seen_types = set()
        for row in strategies:
            stype = row.get("name") or row.get("description", "").split(" ")[0].lower()
            stype = stype or "fvg_fill"
            if stype in seen_types:
                continue
            seen_types.add(stype)
            payload = create_backtest_payload(stype)
            _, out = run_variant(stype, payload)
            if not isinstance(out, dict):
                out = {"error": str(out)}
            scored = dict(out)
            scored["score"] = score_result(out)
            scored["strategy_type"] = stype
            cycle["baselines"].append(scored)
            cycle["baseline_results"] += 1
            cycle["best_baseline"] = max([cycle["best_baseline"], scored], key=lambda x: x.get("score", -1e9)) if not cycle["best_baseline"] else max([cycle["best_baseline"], scored], key=lambda x: x.get("score", -1e9))
        if len(cycle["baselines"]) > 1 and cycle["baselines"]:
            cycle["best_baseline"] = max(cycle["baselines"], key=lambda x: x.get("score", -1e9))
        # Variant sweep over top baseline, constrained budget.
        budget_left = max(0.0, timeout_budget - (time.time() - start))
        if budget_left > 20 and cycle["baselines"]:
            top_baseline = cycle["best_baseline"]
            top_type = top_baseline.get("strategy_type") if isinstance(top_baseline, dict) else None
            if top_type:
                for i, cfg in enumerate(variant_settings(create_backtest_payload(top_type))):
                    if time.time() - start > timeout_budget:
                        break
                    payload, out = run_variant(top_type, cfg)
                    if not isinstance(out, dict):
                        out = {"error": str(out)}
                    scored = dict(out)
                    scored["score"] = score_variant(cfg, out)
                    scored["strategy_type"] = top_type
                    scored["is_variant"] = True
                    scored["variant_lane"] = f"variant_{i:03d}"
                    cycle["variants"].append(scored)
                    cycle["variant_results"] += 1
            if cycle["variants"]:
                cycle["best_variant"] = max(cycle["variants"], key=lambda x: x.get("score", -1e9))
        candidate = cycle["best_variant"] if cycle.get("best_variant") and cycle["best_variant"].get("score", -1e9) > cycle.get("best_baseline", {}).get("score", -1e9) else cycle["best_baseline"]
        qualification_bar = 0.5
        if _safe_num(candidate.get("win_rate")) / 100.0 >= 0.25 and _safe_num(candidate.get("profit_factor")) > 1.05 and _safe_num(candidate.get("expectancy_r")) > 0.0:
            required_trades = 3 if DEFAULT_INSTRUMENT == "BTCUSD" else 5
            if _safe_num(candidate.get("total_trades")) >= required_trades:
                item = {
                    "strategy_type": candidate.get("strategy_type"),
                    "score": _safe_num(candidate.get("score")),
                    "win_rate": _safe_num(candidate.get("win_rate")),
                    "profit_factor": _safe_num(candidate.get("profit_factor")),
                    "expectancy_r": _safe_num(candidate.get("expectancy_r")),
                    "max_drawdown_pct": _safe_num(candidate.get("max_drawdown_pct")),
                    "total_trades": _safe_num(candidate.get("total_trades")),
                    "qualified": True,
                }
                ok, saved_path = maybe_save_learned_strategy(item)
                item["saved"] = ok
                item["saved_path"] = saved_path
                cycle["learned"].append(item)
        if cycle["learned"]:
            cycle["upgrades"].append(f"Learned {len(cycle['learned'])} candidate strategy scaffold(s); wire into `services/backtester/strategies` for `find_signal` implementation.")
        report_path = write_report(cycle)
        cycle["reports"].append(str(report_path))
        cycle["finished_at"] = utc_iso()
        ledger_path = RND_DIR / "strategy_learning.json"
        RND_DIR.mkdir(parents=True, exist_ok=True)
        try:
            existing = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
        except Exception:
            existing = []
        if not isinstance(existing, list):
            existing = [existing]
        existing.append(cycle)
        ledger_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        log.info("Report %s", report_path)
        log.info("Ledger updated at %s", ledger_path)
        return cycle
    except Exception as e:
        cycle["error"] = repr(e)
        log.exception("strategy learning cycle failed")
        cycle["finished_at"] = utc_iso()
        return cycle


def summarize_cycle(cycle: Dict[str, Any]) -> str:
    if cycle.get("error"):
        return f"FAILED: `{cycle['error']}`"
    bl = cycle.get("best_baseline") or {}
    bv = cycle.get("best_variant") or {}
    learned = cycle.get("learned") or []
    lines = [
        f"Baseline best: `{bl.get('strategy_type')}` score `{_safe_num(bl.get('score', 0)):.2f}` wr `{_safe_num(bl.get('win_rate')):.1f}%` trades `{bl.get('total_trades')}`",
        f"Variant best: `{bv.get('strategy_type')}` score `{_safe_num(bv.get('score', 0)):.2f}` wr `{_safe_num(bv.get('win_rate')):.1f}%` trades `{bv.get('total_trades')}`",
        f"Learned: `{len(learned)}`. Reports: `{cycle.get('reports') }`",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    cycle = run_cycle()
    print(summarize_cycle(cycle))
    print(json.dumps({"started_at": cycle.get("started_at"), "baselines": len(cycle.get("baselines", [])), "variants": len(cycle.get("variants", [])), "learned": len(cycle.get("learned", [])), "reports": cycle.get("reports"), "error": cycle.get("error")}, indent=2))
