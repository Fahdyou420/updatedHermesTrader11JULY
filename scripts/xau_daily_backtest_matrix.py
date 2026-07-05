"""Daily XAUUSD strategy matrix backtest from 2020-01-01 to 2026-06-03 via yfinance proxy GC=F."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

REPO = Path('C:/Users/user/Desktop/hermes_claude')
RND = REPO / 'data' / 'rnd'
REPORTS = REPO / 'reports'
STRAT = REPO / 'data' / 'strategies'
RND.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)
STRAT.mkdir(parents=True, exist_ok=True)


def fetch(start='2020-01-01', end='2026-06-04'):
    df = yf.Ticker('GC=F').history(start=start, end=end, interval='1d', auto_adjust=False)
    df = df.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
    })
    df.index = pd.to_datetime(df.index, utc=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
    return df


def prepare(df: pd.DataFrame):
    # Indicators
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    high = df['high']
    low = df['low']
    tr1 = high - low
    tr2 = (high - df['close'].shift(1)).abs()
    tr3 = (low - df['close'].shift(1)).abs()
    df['atr14'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()

    df['vol_sma20'] = df['volume'].rolling(20).mean()
    df['high20'] = df['high'].rolling(20).max().shift(1)
    df['low20'] = df['low'].rolling(20).min().shift(1)

    # Weekly trend via Friday resample
    w = df[['close']].copy()
    w['week'] = w.index.isocalendar().week
    weekly = df['close'].resample('W-FRI').last().ffill()
    weekly_ema = weekly.ewm(span=20, adjust=False).mean()
    df['weekly_bias'] = np.where(df['close'] > weekly_ema.reindex(df.index, method='ffill'), 1, -1)
    return df.dropna(subset=['atr14', 'ema20', 'weekly_bias', 'vol_sma20'])


def simulate_simple(df: pd.DataFrame):
    # Flat-fee simulator: subtract fixed round-turn cost per trade
    cost = 0.30
    trades = []
    in_pos = False
    entry = sl = tp = 0.0
    entry_idx = 0
    for i in range(len(df)):
        row = df.iloc[i]
        if not in_pos:
            # Pullback into bullish daily EMA20 when weekly bullish
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
            hit_sl = low <= sl
            hit_tp = high >= tp
            if hit_sl and hit_tp:
                # conservative: loss first
                pnl = sl - entry
                outcome = 'sl'
            elif hit_sl:
                pnl = sl - entry
                outcome = 'sl'
            elif hit_tp:
                pnl = tp - entry
                outcome = 'tp'
            else:
                continue
            pnl = pnl - cost
            trades.append({'pnl': pnl, 'outcome': outcome, 'len': i - entry_idx + 1})
            in_pos = False
    return trades


def simulate_breakout(df: pd.DataFrame):
    cost = 0.30
    trades = []
    in_pos = False
    entry = sl = tp = 0.0
    volume_surge = False
    entry_idx = 0
    for i in range(len(df)):
        row = df.iloc[i]
        if not in_pos:
            prev_high = float(row['high20']) if not math.isnan(row['high20']) else 0.0
            breakout = bool(row['close'] > prev_high and prev_high > 0)
            vol_surge = bool(row['volume'] > 1.2 * row['vol_sma20'] and row['vol_sma20'] > 0)
            weekly_bull = bool(row['weekly_bias'] == 1)
            if breakout and vol_surge and weekly_bull:
                in_pos = True
                entry = float(row['open'])
                buffer = 0.5 * float(row['atr14'])
                sl = prev_high - buffer
                tp = entry + 2.0 * float(row['atr14'])
                volume_surge = vol_surge
                entry_idx = i
        else:
            high = float(row['high'])
            low = float(row['low'])
            hit_sl = low <= sl
            hit_tp = high >= tp
            if hit_sl and hit_tp:
                pnl = sl - entry
                outcome = 'sl'
            elif hit_sl:
                pnl = sl - entry
                outcome = 'sl'
            elif hit_tp:
                pnl = tp - entry
                outcome = 'tp'
            else:
                continue
            pnl = pnl - cost
            trades.append({'pnl': pnl, 'outcome': outcome, 'len': i - entry_idx + 1, 'vol_surge': volume_surge})
            in_pos = False
    return trades


def simulate_range_buy(df: pd.DataFrame):
    cost = 0.30
    trades = []
    in_pos = False
    entry = sl = tp = 0.0
    entry_idx = 0
    for i in range(len(df)):
        row = df.iloc[i]
        if not in_pos:
            near_low = float(row['close']) <= float(row['low20']) * 1.01
            bullish = bool(row['close'] > row['open'])
            weekly_bull = bool(row['weekly_bias'] == 1)
            if near_low and bullish and weekly_bull:
                in_pos = True
                entry = float(row['open'])
                sl = float(row['low20']) * 0.999
                tp = entry + 1.5 * float(row['atr14'])
                entry_idx = i
        else:
            high = float(row['high'])
            low = float(row['low'])
            hit_sl = low <= sl
            hit_tp = high >= tp
            if hit_sl and hit_tp:
                pnl = sl - entry
                outcome = 'sl'
            elif hit_sl:
                pnl = sl - entry
                outcome = 'sl'
            elif hit_tp:
                pnl = tp - entry
                outcome = 'tp'
            else:
                continue
            pnl = pnl - cost
            trades.append({'pnl': pnl, 'outcome': outcome, 'len': i - entry_idx + 1})
            in_pos = False
    return trades


def summary(trades):
    if not trades:
        return {'trades': 0, 'win_rate': 0.0, 'total_pnl': 0.0, 'profit_factor': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0}
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
    }


def main():
    df = fetch()
    prep = prepare(df)
    candidates = {
        'pullback': simulate_simple(prep),
        'breakout': simulate_breakout(prep),
        'range_buy': simulate_range_buy(prep),
    }
    results = {}
    for name, trades in candidates.items():
        results[name] = summary(trades)
    print(results)
    best = max(results, key=lambda k: results[k]['profit_factor'] if math.isfinite(results[k]['profit_factor']) else -999)
    print('BEST', best, results[best])
    # Save artifacts
    with open(RND / 'xau_backtest_candidates_2020-2026.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    # Save best strategy pseudo-file
    strat_text = f"""
CONFIG = dict(
    strategy_name='gold_{best}',
    instrument='XAUUSD',
    base_lot=0.01,
    cost_per_trade=0.30,
    # Best on GC=F proxy {df.index.min().date()} -> {df.index.max().date()}
    metrics={results[best]},
)
"""
    (STRAT / f'gold_{best}.py').write_text(strat_text, encoding='utf-8')


if __name__ == '__main__':
    import json
    main()
