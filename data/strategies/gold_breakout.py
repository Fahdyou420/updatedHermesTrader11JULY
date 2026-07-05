
"""
gold_breakout.py
XAUUSD breakout strategy: long-biased breakout on daily + H4 with weekly trend alignment,
ATR-based SL/TP, fixed round-trip cost, and risk-based lot sizing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class BreakoutConfig:
    instrument: str = "XAUUSD"
    base_lot: float = 0.01
    cost_per_trade: float = 0.30
    weekly_ema_span: int = 20
    lookback_high: int = 20
    atr_span: int = 14
    sl_atr_mult: float = 0.5
    tp_atr_mult: float = 2.0
    weekly_bias_min: float = 0.0  # require close >= weekly EMA
    min_risk_per_trade: float = 0.005  # 0.5% balance
    lot_atr_divisor: float = 100.0  # lots = risk_balance / (atr * divisor)


CONFIG = BreakoutConfig()


def _indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # True range + ATR
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    df["atr"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(CONFIG.atr_span).mean()
    df["ema20"] = df["close"].ewm(span=CONFIG.weekly_ema_span, adjust=False).mean()
    df["high20"] = df["high"].rolling(CONFIG.lookback_high).max().shift(1)
    return df


def weekly_bias_series(df: pd.DataFrame) -> pd.Series:
    weekly_close = df["close"].resample("W-FRI").last().ffill()
    w_ema = weekly_close.ewm(span=CONFIG.weekly_ema_span, adjust=False).mean()
    bull = (df["close"] > w_ema.reindex(df.index, method="ffill")).astype(int)
    return bull.reindex(df.index, method="ffill").fillna(0)


def simulate(df: pd.DataFrame, initial_balance: float = 100_000.0) -> Dict:
    df = _indicators(df)
    df["weekly_bull"] = weekly_bias_series(df)
    df = df.dropna(subset=["atr", "ema20", "high20"]).copy()

    balance = float(initial_balance)
    trades: List[Dict] = []
    equity = []
    in_pos = False
    entry = sl = tp = 0.0
    entry_idx = 0
    entry_time = None

    for i in range(len(df)):
        row = df.iloc[i]
        equity.append(balance)
        if not in_pos:
            breakout = bool(row["close"] > row["high20"])
            weekly_bull = bool(row["weekly_bull"] == 1)
            atr = float(row["atr"])
            if breakout and weekly_bull and atr > 0:
                in_pos = True
                entry = float(row["close"])  # enter on close of breakout bar
                buffer = CONFIG.sl_atr_mult * atr
                sl = float(row["high20"]) - buffer
                tp = entry + CONFIG.tp_atr_mult * atr
                risk_per_trade = balance * CONFIG.min_risk_per_trade
                lots = risk_per_trade / max(atr * CONFIG.lot_atr_divisor, 1e-9)
                lots = max(CONFIG.base_lot, round(lots, 2))
                entry_idx = i
                entry_time = row.name
                active_lots = lots
                active_entry = entry
                active_sl = sl
                active_tp = tp
        else:
            high = float(row["high"])
            low = float(row["low"])
            hit_sl = low <= active_sl
            hit_tp = high >= active_tp
            if hit_sl and hit_tp:
                # assume SL hit first for conservative estimate
                pnl = active_sl - active_entry - CONFIG.cost_per_trade
                trades.append({
                    "entry_time": entry_time, "exit_time": row.name,
                    "direction": "BUY", "lots": active_lots,
                    "entry": active_entry, "exit": active_sl,
                    "pnl": pnl, "return_pct": pnl / active_entry * 100,
                    "outcome": "sl",
                })
                balance += pnl
                in_pos = False
            elif hit_tp:
                pnl = active_tp - active_entry - CONFIG.cost_per_trade
                trades.append({
                    "entry_time": entry_time, "exit_time": row.name,
                    "direction": "BUY", "lots": active_lots,
                    "entry": active_entry, "exit": active_tp,
                    "pnl": pnl, "return_pct": pnl / active_entry * 100,
                    "outcome": "tp",
                })
                balance += pnl
                in_pos = False
            elif i == len(df) - 1:
                pnl = float(row["close"]) - active_entry - CONFIG.cost_per_trade
                trades.append({
                    "entry_time": entry_time, "exit_time": row.name,
                    "direction": "BUY", "lots": active_lots,
                    "entry": active_entry, "exit": float(row["close"]),
                    "pnl": pnl, "return_pct": pnl / active_entry * 100,
                    "outcome": "timeout",
                })
                balance += pnl
                in_pos = False
    eq = np.array(equity, dtype=float)
    peak = np.maximum.accumulate(eq)
    max_dd = float(np.max(peak - eq))

    pnls = [t["pnl"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    return {
        "strategy": "gold_breakout",
        "trades": len(trades),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "total_pnl": float(np.sum(pnls)),
        "profit_factor": (float(np.sum(wins)) / abs(float(np.sum(losses)))) if losses and float(np.sum(losses)) != 0 else float("inf"),
        "avg_win": float(np.mean(wins)) if wins else 0.0,
        "avg_loss": float(np.mean(losses)) if losses else 0.0,
        "max_drawdown": max_dd,
        "final_balance": float(balance),
        "trades_list": trades,
        "equity_curve": eq.tolist(),
    }
