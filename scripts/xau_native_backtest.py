"""XAUUSD backtest directly from native MT5 history bars (no Yahoo)."""
from __future__ import annotations

import json, math, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd
import requests

REPO = Path('C:/Users/user/Desktop/hermes_claude')
RND = REPO / 'data' / 'rnd'
REPORTS = REPO / 'reports'
STRAT = REPO / 'data' / 'strategies'
RND.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)
STRAT.mkdir(parents=True, exist_ok=True)

BASE = 'http://localhost:7779/api/native'


def fetch_d1_bars(n=6000):
    r = requests.get(f'{BASE}/latest_bars', params={'instrument': 'XAUUSD', 'tf': 'D1', 'n': n}, timeout=60)
    r.raise_for_status()
    return r.json()


def bars_to_df(bars, start='2020-01-01', end='2026-06-04'):
    rows = []
    for b in bars:
        rows.append({
            'time': pd.Timestamp(b['time'], unit='s', tz='UTC'),
            'open': float(b['open']),
            'high': float(b['high']),
            'low': float(b['low']),
            'close': float(b['close']),
            'volume': float(b.get('tick_volume', 0) or 0),
        })
    df = pd.DataFrame(rows).set_index('time').sort_index()
    start_ts = pd.Timestamp(start, tz='UTC')
    end_ts = pd.Timestamp(end, tz='UTC')
    df = df.loc[(df.index >= start_ts) & (df.index < end_ts)]
    return df


def build_df(df: pd.DataFrame):
    df = df.copy()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    df['atr14'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()
    df['vol_sma20'] = df['volume'].rolling(20).mean()
    df['high20'] = df['high'].rolling(20).max().shift(1)
    weekly_close = df['close'].resample('W-FRI').last().ffill()
    w_ema = weekly_close.ewm(span=20, adjust=False).mean()
    df['weekly_bias'] = np.where(df['close'] > w_ema.reindex(df.index, method='ffill'), 1, -1)
    return df.dropna(subset=['atr14', 'ema20', 'vol_sma20', 'weekly_bias']).copy()


def simulate_breakout(df: pd.DataFrame):
    cost = 0.30
    trades = []
    in_pos = False
    entry = sl = tp = 0.0
    entry_idx = 0
    for i in range(len(df)):
        row = df.iloc[i]
        if not in_pos:
            breakout = bool(row['close'] > row['high20'])
            weekly_bull = bool(row['weekly_bias'] == 1)
            if breakout and weekly_bull:
                in_pos = True
                entry = float(row['open'])
                buffer = 0.5 * float(row['atr14'])
                sl = float(row['high20']) - buffer
                tp = entry + 2.0 * float(row['atr14'])
                entry_idx = i
        else:
            high = float(row['high'])
            low = float(row['low'])
            if low <= sl:
                trades.append({'pnl': sl - entry - cost, 'outcome': 'sl', 'len': i - entry_idx + 1})
                in_pos = False
            elif high >= tp:
                trades.append({'pnl': tp - entry - cost, 'outcome': 'tp', 'len': i - entry_idx + 1})
                in_pos = False
            elif i == len(df) - 1:
                trades.append({'pnl': float(row['close']) - entry - cost, 'outcome': 'timeout', 'len': i - entry_idx + 1})
                in_pos = False
    return trades


def simulate_pullback(df: pd.DataFrame):
    cost = 0.30
    trades = []
    in_pos = False
    entry = sl = tp = 0.0
    entry_idx = 0
    for i in range(len(df)):
        row = df.iloc[i]
        if not in_pos:
            weekly_bull = bool(row['weekly_bias'] == 1)
            pullback = abs(row['close'] - row['ema20']) <= 0.10 * row['atr14']
            if weekly_bull and pullback:
                in_pos = True
                entry = float(row['open'])
                sl = entry - 1.0 * float(row['atr14'])
                tp = entry + 2.0 * float(row['atr14'])
                entry_idx = i
        else:
            high = float(row['high'])
            low = float(row['low'])
            if low <= sl:
                trades.append({'pnl': sl - entry - cost, 'outcome': 'sl', 'len': i - entry_idx + 1})
                in_pos = False
            elif high >= tp:
                trades.append({'pnl': tp - entry - cost, 'outcome': 'tp', 'len': i - entry_idx + 1})
                in_pos = False
            elif i == len(df) - 1:
                trades.append({'pnl': float(row['close']) - entry - cost, 'outcome': 'timeout', 'len': i - entry_idx + 1})
                in_pos = False
    return trades


def summary(trades):
    if not trades:
        return {'trades': 0, 'win_rate': 0.0, 'total_pnl': 0.0, 'profit_factor': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0, 'avg_len': 0}
    pnl = [t['pnl'] for t in trades]
    wins = [p for p in pnl if p > 0]
    losses = [p for p in pnl if p <= 0]
    return {
        'trades': len(trades),
        'win_rate': len(wins) / len(trades),
        'total_pnl': float(np.sum(pnl)),
        'profit_factor': (float(np.sum(wins)) / abs(float(np.sum(losses)))) if losses and float(np.sum(losses)) != 0 else float('inf'),
        'avg_win': float(np.mean(wins)) if wins else 0.0,
        'avg_loss': float(np.mean(losses)) if losses else 0.0,
        'avg_len': float(np.mean([t['len'] for t in trades])),
    }


def run():
    raw = fetch_d1_bars()
    bars_path = RND / 'xau_native_d1_bars_2020_2026.json'
    with open(bars_path, 'w', encoding='utf-8') as f:
        json.dump(raw, f, indent=2)

    df = bars_to_df(raw)
    print('bars_in_range', len(df), 'from', df.index[0].isoformat(), 'to', df.index[-1].isoformat())
    df2 = build_df(df)

    breakout = simulate_breakout(df2)
    pullback = simulate_pullback(df2)
    breakout_sum = summary(breakout)
    pullback_sum = summary(pullback)

    out = {
        'bars_file': str(bars_path),
        'range': {'start': df.index[0].isoformat(), 'end': df.index[-1].isoformat(), 'bars': int(len(df))},
        'breakout': breakout_sum,
        'pullback': pullback_sum,
        'selected': 'BREAKOUT',
    }
    out_path = RND / 'xau_native_backtest_metrics_2020_2026.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)

    print('selected BREAKOUT')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    run()
