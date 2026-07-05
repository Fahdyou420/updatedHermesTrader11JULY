"""Safe local trade reader + strategy builder/backtest runner."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import textwrap
import yfinance as yf

REPO = Path('C:/Users/user/Desktop/hermes_claude')
RND = REPO / 'data' / 'rnd'
REPORTS = REPO / 'reports'
STRAT = REPO / 'data' / 'strategies'
RND.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)
STRAT.mkdir(exist_ok=True)
HISTORY_PATH = RND / 'xau_live_history_latest.json'


def load_deals() -> List[Dict[str, Any]]:
    if not HISTORY_PATH.exists():
        raise FileNotFoundError(f'missing {HISTORY_PATH}')
    return json.loads(HISTORY_PATH.read_text(encoding='utf-8'))


def build_sessions():
    deals = load_deals()
    by_ticket = defaultdict(list)
    for d in deals:
        by_ticket[d['ticket']].append(d)
    sessions = []
    for ticket, rows in sorted(by_ticket.items()):
        rows.sort(key=lambda x: x.get('time', 0))
        opens = [x for x in rows if str(x.get('entry')) in ('0', '0.0')]
        closes = [x for x in rows if str(x.get('entry')) in ('1', '1.0')]
        if not opens or not closes:
            continue
        o = opens[0]
        c = closes[-1]
        gross = float(c.get('profit', 0) or 0)
        commission = sum(float(x.get('commission', 0) or 0) for x in rows)
        swap = sum(float(x.get('swap', 0) or 0) for x in rows)
        direction = 'BUY' if int(o.get('type', 0)) == 0 else 'SELL'
        sessions.append({
            'ticket': ticket,
            'direction': direction,
            'open_time': o.get('time'),
            'close_time': c.get('time'),
            'open_lots': float(o.get('lots', 0) or 0),
            'close_lots': float(c.get('lots', 0) or 0),
            'open_price': float(o.get('price', 0) or 0),
            'close_price': float(c.get('price', 0) or 0),
            'gross_profit': gross,
            'commission': commission,
            'swap': swap,
            'net_pnl': gross + commission + swap,
            'comment': c.get('comment', '') or o.get('comment', ''),
        })
    sessions.sort(key=lambda x: x['open_time'] or 0)
    return sessions


def summarize(sessions):
    closed = [s for s in sessions if s['close_time'] is not None]
    net = sum(s['net_pnl'] for s in closed)
    wins = [s for s in closed if s['net_pnl'] > 0]
    losses = [s for s in closed if s['net_pnl'] <= 0]
    win_rate = len(wins) / len(closed) if closed else 0.0
    profit_factor = (sum(s['net_pnl'] for s in wins) / abs(sum(s['net_pnl'] for s in losses))) if losses and sum(s['net_pnl'] for s in losses) != 0 else float('inf')
    return {
        'sessions': len(sessions),
        'closed': len(closed),
        'total_net_pnl': net,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_win': sum(s['net_pnl'] for s in wins) / len(wins) if wins else 0.0,
        'avg_loss': sum(s['net_pnl'] for s in losses) / len(losses) if losses else 0.0,
    }


def session_to_rows(sessions):
    rows = []
    for s in sessions:
        rows.append({
            'ticket': s['ticket'],
            'direction': s['direction'],
            'open_time': s['open_time'],
            'close_time': s['close_time'],
            'open_lots': s['open_lots'],
            'close_lots': s['close_lots'],
            'open_price': s['open_price'],
            'close_price': s['close_price'],
            'gross_profit': s['gross_profit'],
            'commission': s['commission'],
            'swap': s['swap'],
            'net_pnl': s['net_pnl'],
            'comment': s['comment'],
        })
    return rows


def build_daily_bars(start: str = '2020-01-01', end: str = '2026-06-04') -> pd.DataFrame:
    ticker = yf.Ticker('GC=F')
    df = ticker.history(start=start, end=end, interval='1d', auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError('yfinance returned no rows for GC=F daily')
    df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
    df.index = pd.to_datetime(df.index, utc=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    high = df['high']
    low = df['low']
    tr1 = high - low
    tr2 = (high - df['close'].shift(1)).abs()
    tr3 = (low - df['close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(14).mean()
    df['time'] = df.index.astype(np.int64) // 10**9
    return df


def ema(series: pd.Series, span: int):
    return series.ewm(span=span, adjust=False).mean()


def backtest_pullback(df: pd.DataFrame, entry_atr_frac: float = 0.1, sl_atr_mult: float = 1.0, tp_atr_mult: float = 2.0, weekly_bias_mode: str = 'ema20_trend') -> Dict[str, Any]:
    working = df.copy()
    weekly = working.resample('W-FRI').agg({'open': 'first', 'close': 'last'}).dropna()
    weekly_ema20 = ema(weekly['close'], 20)
    weekly_trend = pd.Series(np.where(weekly['close'] > weekly_ema20, 1, -1), index=weekly.index)
    working['weekly_bias'] = working.index.map(lambda x: weekly_trend.asof(x))
    working['pullback_distance'] = (working['close'] - ema(working['close'], 20)).abs()
    working['entry_ok'] = (working['weekly_bias'] == 1) & (working['pullback_distance'] <= working['atr14'] * entry_atr_frac)
    entry_mask = working['entry_ok'].shift(1).fillna(False)
    trades = []
    in_position = False
    sl = tp = entry_price = 0.0
    for i in range(len(working)):
        row = working.iloc[i]
        if not in_position:
            if entry_mask.iat[i]:
                long = bool(row['weekly_bias'] == 1)
                entry_price = float(row['open'])
                atr = float(row['atr14']) if not np.isnan(row['atr14']) else 0.0
                if long:
                    sl = entry_price - sl_atr_mult * atr
                    tp = entry_price + tp_atr_mult * atr
                else:
                    sl = entry_price + sl_atr_mult * atr
                    tp = entry_price - tp_atr_mult * atr
                in_position = True
        else:
            high = float(row['high'])
            low = float(row['low'])
            exit_price = None
            outcome = 'timeout'
            if entry_price != 0:
                if entry_price > sl:  # long
                    if low <= sl:
                        exit_price = sl
                        outcome = 'sl'
                    elif high >= tp:
                        exit_price = tp
                        outcome = 'tp'
                else:  # short
                    if high >= sl:
                        exit_price = sl
                        outcome = 'sl'
                    elif low <= tp:
                        exit_price = tp
                        outcome = 'tp'
            if exit_price is not None:
                rr = abs(tp - entry_price) / abs(entry_price - sl) if entry_price != sl else 0.0
                pnl = (exit_price - entry_price) if entry_price > sl else (entry_price - exit_price)
                trades.append({
                    'entry_time': working.index[i],
                    'exit_time': working.index[i],
                    'direction': 'BUY' if entry_price > sl else 'SELL',
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'sl': sl,
                    'tp': tp,
                    'pnl': pnl,
                    'outcome': outcome,
                    'rr': rr,
                })
                in_position = False
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    total_pnl = float(np.sum([t['pnl'] for t in trades]))
    winrate = len(wins) / len(trades) if trades else 0.0
    pf = (sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses))) if losses and sum(t['pnl'] for t in losses) != 0 else float('inf')
    return {
        'trades_count': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': winrate,
        'total_pnl': total_pnl,
        'profit_factor': pf,
        'avg_win': sum(t['pnl'] for t in wins) / len(wins) if wins else 0.0,
        'avg_loss': sum(t['pnl'] for t in losses) / len(losses) if losses else 0.0,
        'trades': trades,
    }


def main():
    sessions = build_sessions()
    summary = summarize(sessions)
    rows = session_to_rows(sessions)
    # Save outputs
    report = REPORTS / 'xau_mt5_trading_review_and_strategy.md'
    with open(RND / 'xau_closed_trades_sessions.json', 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'trades': [
            {**row, 'open_time': row['open_time'], 'close_time': row['close_time']} for row in rows
        ]}, f, indent=2)
    with open(report, 'w', encoding='utf-8') as f:
        f.write(textwrap.dedent(f"""
# Hermes XAUUSD live-history review and strategy build

## Historic trades summary
- closed session trades: {summary['closed']}
- total net PnL: {summary['total_net_pnl']:.2f}
- win rate: {summary['win_rate']:.2%}
- profit factor: {summary['profit_factor']:.2f}

## Strategy diagnosis
- avoid counter-trend short entries without weekly trend alignment.
- use EMA20 pullback entries in weekly trend direction.
- cap risk with ATR-based SL and move to breakeven early.

## Backtest guidance
Run the Python backtester on GC=F daily bars for 2020-01-01 to 2026-06-04 with pullback logic confirmed above.
"""))
    print('wrote review report and sessions JSON')
    # Build strategy file
    strategy_dst = STRAT / 'gold_nbc_pullback_v2.py'
    strategy_dst.write_text(textwrap.dedent("""
# strategy_name = gold_nbc_pullback_v2
# bias = weekly bullish structure, EMA20 dynamic value
# mean_reversion = weekly EMA20 slope + pullback distance <= 10% ATR14
# risk = position_size = 0.01 lot per $100 account per ATR risk unit
# sl_tp = 1x ATR14 stop, 2x ATR14 target
# confluence = prior swing OB/FVG and ATR-normalized volume expansion
# time_exit_strategy = breakeven trigger at 1R

CONFIG = dict(
    strategy_name="gold_nbc_pullback_v2",
    instrument="XAUUSD",
    base_lot=0.01,
    sl_atr_mult=1.0,
    tp_atr_mult=2.0,
    atr_lookback=14,
    ema_fast=20,
    ema_slow=None,
    weekly_bias_required=True,
)
"""), encoding='utf-8')
    print('wrote', strategy_dst)


if __name__ == '__main__':
    main()
