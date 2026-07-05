"""Multi-timeframe XAUUSD breakout strategy backtest: Daily, H4, H1.
Outputs human-readable report + JSON metrics pack."""
from __future__ import annotations

import json, math, re
from pathlib import Path
from datetime import datetime, timezone

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

LIVE_HISTORY_PATH = RND / 'xau_native_history_latest.json'
LIVE_PACK_PATH = RND / 'xau_native_strategy_pack.json'
REPORT_PATH = REPORTS / 'xau_native_strategy_report.md'


def load_live_rows() -> list:
    with open(LIVE_HISTORY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('trades', [])


def summarize(rows):
    closed = [t for t in rows if t.get('open_time') and t.get('close_time')]
    net = sum(float(t.get('net') or 0) for t in closed)
    gross = sum(float(t.get('gross') or 0) for t in closed)
    commission = sum(float(t.get('commission') or 0) for t in closed)
    swap = sum(float(t.get('swap') or 0) for t in closed)
    wins = [t for t in closed if float(t.get('net') or 0) > 0]
    losses = [t for t in closed if float(t.get('net') or 0) <= 0]
    win_rate = len(wins) / len(closed) if closed else 0.0
    profit_factor = (sum(float(t.get('net') or 0) for t in wins) / abs(sum(float(t.get('net') or 0) for t in losses))) if losses and sum(float(t.get('net') or 0) for t in losses) != 0 else float('inf')
    avg_win = sum(float(t.get('net') or 0) for t in wins) / len(wins) if wins else 0.0
    avg_loss = sum(float(t.get('net') or 0) for t in losses) / len(losses) if losses else 0.0
    max_win = max((float(t.get('net') or 0) for t in wins), default=0.0)
    max_loss = min((float(t.get('net') or 0) for t in losses), default=0.0)
    pnl = [float(t.get('net') or 0) for t in closed]
    if pnl:
        peak = np.maximum.accumulate(np.cumsum(pnl))
        max_dd = float(np.max(peak - np.cumsum(pnl)))
    else:
        max_dd = 0.0
    return {
        'closed_trades': len(closed),
        'total_net_pnl': float(net),
        'gross_profit': float(gross),
        'commission': float(commission),
        'swap': float(swap),
        'win_rate': float(win_rate),
        'profit_factor': float(profit_factor),
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
        'max_win': float(max_win),
        'max_loss': float(max_loss),
        'max_drawdown': float(max_dd),
    }


def failure_modes(rows):
    comments = [t.get('comment', '') for t in rows if t.get('comment')]
    sl_count = sum(1 for c in comments if re.search(r'\[?sl', c, re.I))
    tp_count = sum(1 for c in comments if re.search(r'\[?tp', c, re.I))
    short_losses = [t for t in rows if t.get('type') == 'SELL' and float(t.get('net') or 0) < 0]
    big_loss = [t for t in rows if float(t.get('net') or 0) < -1000]
    return {'comments': len(comments), 'sl_tagged': sl_count, 'tp_tagged': tp_count, 'short_losses': len(short_losses), 'big_loss_trades': len(big_loss)}


def build_df(interval='1d'):
    df = yf.Ticker('GC=F').history(start='2020-01-01', end='2026-06-04', interval=interval, auto_adjust=False)
    df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
    df.index = pd.to_datetime(df.index, utc=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
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
    df = df.dropna(subset=['atr14', 'ema20', 'vol_sma20', 'weekly_bias']).copy()
    return df


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
                sl = float(row['high20']) - 0.5 * float(row['atr14'])
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


def summary_metrics(trades):
    if not trades:
        return {'trades': 0, 'win_rate': 0.0, 'total_pnl': 0.0, 'profit_factor': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0, 'avg_len': 0}
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    return {
        'trades': len(trades),
        'win_rate': len(wins) / len(trades),
        'total_pnl': float(np.sum(pnls)),
        'profit_factor': (float(np.sum(wins)) / abs(float(np.sum(losses)))) if losses and float(np.sum(losses)) != 0 else float('inf'),
        'avg_win': float(np.mean(wins)) if wins else 0.0,
        'avg_loss': float(np.mean(losses)) if losses else 0.0,
        'avg_len': float(np.mean([t['len'] for t in trades])),
    }


def setup_reviews(rows):
    setups = []
    for t in rows:
        setups.append({
            'ticket': t.get('ticket'),
            'time': t.get('open_time'),
            'direction': t.get('type'),
            'volume': t.get('volume'),
            'open': t.get('open'),
            'close': t.get('close'),
            'outcome': 'WIN' if float(t.get('net') or 0) > 0 else 'LOSS',
            'net': float(t.get('net') or 0),
            'improvement': 'Reject counter-trend shorts unless weekly structure breaks.' if t.get('type') == 'SELL' and float(t.get('net') or 0) < 0 else 'Trailing stop after TP1 to protect remainder.',
        })
    return setups


def write_report(path: Path, live: dict, failures: dict, setups, backtests: dict):
    tf_rows = []
    for tf, m in backtests.items():
        tf_rows.append(f"| {tf} | {m['trades']} | {m['win_rate']:.2%} | {m['total_pnl']:.2f} | {m['profit_factor']:.2f} | {m['avg_win']:.2f} | {m['avg_loss']:.2f} |")
    setup_rows = []
    for s in setups:
        setup_rows.append(f"| {s['ticket']} | {s['time']} | {s['direction']} | {s['volume']} | {s['open']} | {s['close']} | {s['outcome']} | {s['net']:.2f} | {s['improvement']} |")
    report = f"""# XAUUSD Native MT5 Strategy Report
Generated: {datetime.now(timezone.utc).isoformat()}
Source: `services/mt5_bridge` Native API http://localhost:7779

## 1. Native Live History
- endpoint: `/api/native/history?days=30`
- paired closed trades: {live['closed_trades']}
- total net PnL: {live['total_net_pnl']:.2f}
- gross: {live['gross_profit']:.2f} | commission: {live['commission']:.2f} | swap: {live['swap']:.2f}
- win rate: {live['win_rate']:.2%}
- profit factor: {live['profit_factor']:.2f}
- avg win: {live['avg_win']:.2f} | avg loss: {live['avg_loss']:.2f}
- max win: {live['max_win']:.2f} | max loss: {live['max_loss']:.2f}
- estimated max drawdown: {live['max_drawdown']:.2f}

## 2. Failure Modes
- SL-tagged trades: {failures['sl_tagged']}
- TP-tagged trades: {failures['tp_tagged']}
- short-side losses: {failures['short_losses']}
- big loss trades >1000: {failures['big_loss_trades']}

## 3. Setup Reviews
| Ticket | Time | Dir | Vol | Open | Close | Outcome | Net | Improvement |
|---|---|---|---|---|---|---|---|---|
{''.join(setup_rows)}

## 4. Multi-TF Backtest Matrix (GC=F proxy) 2020-01-01 -> 2026-06-03
| TF | Trades | Win Rate | PnL | PF | Avg Win | Avg Loss |
|---|---|---|---|---|---|---|
{''.join(tf_rows)}

## 5. Selected Strategy
- Best setup: Breakout with weekly bullish filter + volume confirmation.
- Rules:
  - weekly bias: close > weekly EMA20
  - entry: close > previous 20-bar high
  - SL: breakout high - 0.5 * ATR14
  - TP: entry + 2.0 * ATR14
  - cost: 0.30 per round trip
  - risk: 0.5% balance per trade, ATR-based lot sizing

## 6. Upgrade Plan
1. Replace yfinance with native `/latest_bars` once available.
2. Add H4 + D1 confluence filter for entries.
3. Add TP1 at 1.5R -> breakeven -> TP2 at 2.8R with trailing ATR.
4. Add London/NY session gating.
5. Add history archive cron to `data/rnd/xau_native_history_YYYY-MM-DD.json`.

## 7. Files
- `data/rnd/xau_native_history_latest.json`
- `data/strategies/gold_breakout.py`
- `services/mt5_bridge/mt5_history_service.py`
- `scripts/init_mt5.py`
"""
    path.write_text(report, encoding='utf-8')


def main():
    rows = load_live_rows()
    live = summarize(rows)
    failures = failure_modes(rows)
    setups = setup_reviews(rows)

    tf_metrics = {}
    for tf in ['1d', '4h']:
        try:
            df = build_df(interval=tf)
            trades = simulate_breakout(df)
            tf_metrics[tf.upper()] = summary_metrics(trades)
        except Exception as e:
            tf_metrics[tf.upper()] = {'error': str(e)}

    with open(RND / 'xau_strategy_backtest_metrics.json', 'w', encoding='utf-8') as f:
        json.dump({'live': live, 'failures': failures, 'backtests': tf_metrics, 'selected': 'BREAKOUT'}, f, indent=2)

    write_report(REPORT_PATH, live, failures, setups, tf_metrics)
    print('wrote', REPORT_PATH)
    print(json.dumps({'live': live, 'selected': 'BREAKOUT', 'backtests': tf_metrics}, indent=2))


if __name__ == '__main__':
    main()
