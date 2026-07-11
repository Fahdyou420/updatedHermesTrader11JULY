from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path(os.path.dirname(os.path.abspath(__file__))).parent
SPRINT_ROOT = REPO / "data" / "sprint"
VAULT_ROOT = REPO / "data" / "obsidian" / "03_TRADE_JOURNAL" / "sprint_decisions"
BASE = "http://127.0.0.1:7779/api/native"
SYMBOL = "XAUUSD"
TFs = ["M1", "M5", "M15", "H4", "D1", "W1"]


@dataclass
class SetupDecision:
    cycle_ts: str
    setup_type: str
    direction: str
    action: str
    htf_bias: str
    ltf_trigger: str
    confluence: list[str]
    reason: str
    metadata: dict


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def native_bars(tf: str, n: int = 2000) -> list[dict]:
    r = requests.get(f"{BASE}/latest_bars", params={"instrument": SYMBOL, "tf": tf, "n": n}, timeout=30)
    r.raise_for_status()
    return r.json()


def _ema(values: list[float], span: int) -> list[float]:
    out: list[float] = []
    k = 2.0 / (span + 1)
    prev = values[0] if values else 0.0
    for v in values:
        prev = v * k + prev * (1 - k)
        out.append(prev)
    return out


def _atr14(bars: list[dict]) -> list[float]:
    tr: list[float] = []
    for i, b in enumerate(bars):
        if i == 0:
            tr.append(float(b["high"]) - float(b["low"]))
            continue
        prev = bars[i - 1]
        tr.append(
            max(
                float(b["high"]) - float(b["low"]),
                abs(float(b["high"]) - float(prev["close"])),
                abs(float(b["low"]) - float(prev["close"])),
            )
        )
    out: list[float] = []
    for i, v in enumerate(tr):
        out.append(sum(tr[max(0, i - 13) : i + 1]) / min(i + 1, 14))
    return out


def htf_bias(h4: list[dict], d1: list[dict], w1: list[dict]) -> tuple[str, list[str]]:
    signals: list[str] = []
    score = 0.0
    if len(h4) >= 20:
        closes = [float(b["close"]) for b in h4]
        v = _ema(closes, 20)[-1]
        signals.append(f"H4 ema20={v:.2f}")
        score += 1 if closes[-1] > v else -1
    if len(d1) >= 20:
        closes = [float(b["close"]) for b in d1]
        v = _ema(closes, 20)[-1]
        signals.append(f"D1 ema20={v:.2f}")
        score += 1 if closes[-1] > v else -1
    if len(w1) >= 5:
        highs = [float(b["high"]) for b in w1[-5:]]
        lows = [float(b["low"]) for b in w1[-5:]]
        hh = max(highs[-3:]) > max(highs[:2])
        hl = min(lows[-3:]) > min(lows[:2])
        signals.append("W1 HH" if hh else "W1 not HH")
        signals.append("W1 HL" if hl else "W1 not HL")
        score += (1 if hh else -1) + (1 if hl else -1)
    if score >= 2:
        return "bullish", signals
    if score <= -2:
        return "bearish", signals
    return "neutral", signals


def ltf_setup(m1: list[dict], m5: list[dict], m15: list[dict], bias: str) -> tuple[str, str, list[str]]:
    reason = "no aligned entry trigger"
    trigger = "none"
    confluences: list[str] = []
    if bias == "bullish" and len(m15) > 12 and len(m5) > 3 and len(m1) > 3:
        swing_low = min(float(b["low"]) for b in m15[-12:])
        reclaim = any(float(b["close"]) > swing_low for b in m15[-4:])
        if reclaim:
            trigger = "M15 reclaim of swing-low OB"
            confluences.append("reclaims recent swing low")
            if (
                float(m15[-1]["close"]) > float(m15[-2]["open"])
                and float(m15[-1]["open"]) < float(m15[-2]["close"])
                and float(m15[-1]["close"]) > float(m15[-2]["close"])
            ):
                confluences.append("bullish engulf")
            return "bullish_ob", trigger, confluences + ["aligned bullish HTF + LTF reclaim"]
    if bias == "bearish" and len(m15) > 12 and len(m5) > 3 and len(m1) > 3:
        swing_high = max(float(b["high"]) for b in m15[-12:])
        fail = any(float(b["close"]) < swing_high for b in m15[-4:])
        if fail:
            trigger = "M15 failure below swing-high OB"
            confluences.append("rejects recent swing high")
            if (
                float(m15[-1]["close"]) < float(m15[-2]["open"])
                and float(m15[-1]["open"]) > float(m15[-2]["close"])
                and float(m15[-1]["close"]) < float(m15[-2]["close"])
            ):
                confluences.append("bearish engulf")
            return "bearish_ob", trigger, confluences + ["aligned bearish HTF + LTF rejection"]
    return "none", trigger, confluences + [reason]


def _utc_hour() -> int:
    return int(datetime.now(timezone.utc).strftime("%H"))


def _safe_ts(ts: str) -> str:
    return ts.replace(":", "-").replace(".", "-")



def append_decision(decision: SetupDecision) -> None:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    vault_dir = VAULT_ROOT / day
    vault_dir.mkdir(parents=True, exist_ok=True)
    safe_ts = decision.cycle_ts.replace(":", "-").replace(".", "-").replace("+", "-")
    path = vault_dir / f"{safe_ts}_{decision.setup_type}_{decision.direction}.md"
    body = "\n".join(
        [
            f"# {decision.setup_type} {decision.action} — {decision.cycle_ts}",
            "",
            "## Decision",
            f"- action: {decision.action}",
            "",
            "## Bias",
            f"- htf_bias: {decision.htf_bias}",
            "",
            "## Trigger",
            f"- ltf_trigger: {decision.ltf_trigger}",
            "",
            "## Confluence",
            *[f"- {item}" for item in decision.confluence],
            "",
            "## Reason",
            decision.reason,
            "",
            "## Metadata",
            "```json",
            json.dumps(decision.metadata, indent=2),
            "```",
        ]
    )
    path.write_text(body, encoding="utf-8")
    (SPRINT_ROOT / "latest_lane1_decision.md").write_text(body, encoding="utf-8")


def append_log(text: str) -> None:
    ts = _iso()
    line = json.dumps({"ts": ts, "text": text}, ensure_ascii=False)
    log_path = SPRINT_ROOT / "lane1.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def submit_paper_trade(direction: str, entry: float, sl: float, tp: float, atr: float, reason: str) -> None:
    risk_balance = 97749.38 * 0.005
    lots = max(0.01, round(risk_balance / max(atr * 100.0, 1e-9), 2))
    payload = {
        "signal_id": f"lane1_{int(time.time()*1000)}",
        "instrument": SYMBOL,
        "direction": direction.upper(),
        "entry_price": entry,
        "entry_type": "market",
        "sl": sl,
        "tp": tp,
        "lots": lots,
        "timeframe": "M15",
        "strategy_id": "lane1_mtf_auto",
        "setup_type": "mtf_auto",
        "session": "overlap",
        "mode": "paper",
        "r_ratio": 2.0,
        "confidence": "medium",
        "agent_notes": reason,
        "status": "pending",
    }
    r = requests.post("http://127.0.0.1:5561/signal", json=payload, timeout=20)
    append_log(f"paper_signal {direction} status={r.status_code} resp={r.text[:200]}")


def cycle() -> None:
    ts = _iso()
    try:
        bars = {tf: native_bars(tf) for tf in TFs}
    except Exception as e:
        append_log(f"bars_error={e}")
        return
    bias, bias_signals = htf_bias(bars["H4"], bars["D1"], bars["W1"])
    setup_type, trigger, confluences = ltf_setup(bars["M1"], bars["M5"], bars["M15"], bias)
    meta = {
        "bars": {k: len(v) for k, v in bars.items()},
        "bias_signals": bias_signals,
        "last_m15_close": float(bars["M15"][-1]["close"]) if bars["M15"] else None,
    }
    action = "REJECT"
    if setup_type.startswith("bullish") and bias == "bullish":
        action = "BUY"
    elif setup_type.startswith("bearish") and bias == "bearish":
        action = "SELL"
    reason = f"bias={bias} setup={setup_type} action={action}"
    decision = SetupDecision(
        cycle_ts=ts,
        setup_type=setup_type,
        direction=bias if action in ("BUY", "SELL") else bias,
        action=action,
        htf_bias=bias,
        ltf_trigger=trigger,
        confluence=confluences,
        reason=reason,
        metadata=meta,
    )
    append_decision(decision)
    append_log(f"decision action={action} setup={setup_type} bias={bias}")
    if action in ("BUY", "SELL"):
        entry = float(bars["M15"][-1]["close"])
        atr_arr = _atr14(bars["M15"])
        atr = float(atr_arr[-1]) if atr_arr else 0.0
        if atr > 0:
            sl = entry - 1.5 * atr if action == "BUY" else entry + 1.5 * atr
            tp = entry + 3.0 * atr if action == "BUY" else entry - 3.0 * atr
            submit_paper_trade(action, entry, sl, tp, atr, reason)
    try:
        r = requests.get(f"{BASE}/positions", timeout=20)
        positions = r.json() if r.ok else []
    except Exception as e:
        positions = []
        append_log(f"open_positions_error={e}")
    if isinstance(positions, dict):
        positions = positions.get("positions", []) if isinstance(positions.get("positions"), list) else []
    append_log(f"open_positions={len(positions)} bias={bias}")
    session = "london" if 7 <= _utc_hour() <= 11 else ("ny" if 12 <= _utc_hour() <= 16 else "asian")
    if action in ("BUY", "SELL") and any(
        (p.get("direction", "").lower() == action.lower() if isinstance(p, dict) else False) and p.get("strategy_id") == "lane1_mtf_auto"
        for p in positions
    ):
        append_log(f"blocked_duplicate_direction action={action}")
        return
    if action in ("BUY", "SELL") and len(positions) >= 5:
        append_log(f"blocked_max_positions action={action} open={len(positions)}")
        return


def main() -> None:
    append_log("lane1_started")
    cycles = 1
    try:
        cycles = max(1, int(os.environ.get('LANE1_CYCLES', '1')))
    except Exception:
        cycles = 1
    for _ in range(cycles):
        cycle()
        time.sleep(15 * 60)



if __name__ == "__main__":
    main()
