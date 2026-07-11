"""Local AMD/PO3 backtester for XAUUSD M15, optimized version."""
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

CSV_M15 = Path(r'C:/Users/user/Desktop/hermes_claude/data/market_data/local_xau_m15.csv')
OUT = Path(r'C:/Users/user/Desktop/hermes_claude/data/rnd/results/strategy_amd_po3_M15.json')
INITIAL_EQUITY = 10000.0
RISK_PCT = 0.01


def load(path, max_bars=None):
    df = pd.read_csv(path, sep='\t')
    df.columns = [c.strip() for c in df.columns]
    df['date'] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'], dayfirst=False)
    df = df.sort_values('date').reset_index(drop=True)
    if max_bars:
        df = df.tail(max_bars).reset_index(drop=True)
    return {
        'date': df['date'].values,
        'open': df['<OPEN>'].astype(float).values,
        'high': df['<HIGH>'].astype(float).values,
        'low': df['<LOW>'].astype(float).values,
        'close': df['<CLOSE>'].astype(float).values,
    }


def rolling_range(low, high, window=30):
    low_min = pd.Series(low).rolling(window, min_periods=window).min().values
    high_max = pd.Series(high).rolling(window, min_periods=window).max().values
    return low_min, high_max


def detect_manip(high, low, close, window=30):
    h_std = pd.Series(high).rolling(window).std(ddof=0).values
    l_std = pd.Series(low).rolling(window).std(ddof=0).values
    manip_idx = []
    for i in range(window, len(close) - 1):
        if h_std[i] and l_std[i]:
            ng_low = low[i] < low[i - 1] - l_std[i]
            ng_high = high[i] > high[i - 1] + h_std[i]
        else:
            ng_low = False
            ng_high = False
        if ng_low or ng_high:
            manip_idx.append(i)
    return manip_idx


def detect_ifvg(open_, high, low, close):
    ifvgs = []
    for i in range(2, len(close)):
        c1, h1, l1 = close[i - 2], high[i - 2], low[i - 2]
        c2 = close[i - 1]
        c3, l3, h3 = close[i], low[i], high[i]
        if c2 > h1 and l3 < h1:
            ifvgs.append((i, 'bullish', max(l1, low[i - 1]), h1))
        elif c2 < l1 and h3 > l1:
            ifvgs.append((i, 'bearish', l1, min(h1, high[i - 1])))
    return ifvgs


def run():
    data = load(CSV_M15, max_bars=20000)
    date = data['date']
    open_ = data['open']
    high = data['high']
    low = data['low']
    close = data['close']
    n = len(close)
    low_min, high_max = rolling_range(low, high)
    manip_idx = set(detect_manip(high, low, close))
    ifvgs = detect_ifvg(open_, high, low, close)
    ifvg_map = {}
    for idx, typ, f_low, f_high in ifvgs:
        ifvg_map[idx] = {'low': f_low, 'high': f_high, 'type': typ}

    trades = []
    equity = INITIAL_EQUITY
    peak_equity = equity
    in_trade = False
    trade = None
    last_ifvg_idx = 0

    for i in range(60, n):
        if in_trade:
            trade['bars'] += 1
            hit_sl = low[i] <= trade['sl']
            hit_tp = high[i] >= trade['tp']
            close_reason = None
            if hit_sl and hit_tp:
                close_reason = 'sl' if abs(trade['sl'] - close[i]) < abs(trade['tp'] - close[i]) else 'tp'
            elif hit_sl:
                close_reason = 'sl'
            elif hit_tp:
                close_reason = 'tp'
            elif trade['bars'] >= 24:
                close_reason = 'timebar'
            if close_reason:
                px = float(close[i])
                pnl_r = -1.0 if close_reason == 'sl' else (float(trade['rr']) if close_reason == 'tp' else 0.0)
                pnl_usd = pnl_r * RISK_PCT * equity
                equity += pnl_usd
                trades.append(
                    {
                        'entry_time': str(date[trade['entry_idx']]),
                        'exit_time': str(date[i]),
                        'direction': 'BUY',
                        'entry': float(trade['entry']),
                        'exit': px,
                        'sl': float(trade['sl']),
                        'tp': float(trade['tp']),
                        'pnl_r': float(pnl_r),
                        'pnl_usd': float(pnl_usd),
                        'bars': trade['bars'],
                        'close_reason': close_reason,
                    }
                )
                in_trade = False
                trade = None
                if equity > peak_equity:
                    peak_equity = equity
            continue

        px = float(close[i])
        if np.isnan(low_min[i]) or np.isnan(high_max[i]):
            continue
        if not (low_min[i] <= px <= high_max[i]):
            continue
        if i not in manip_idx:
            continue
        f = ifvg_map.get(i, None)
        if f is None:
            continue
        if not (f['low'] <= px <= f['high']):
            continue
        if px <= f['low'] * 1.0005:
            continue
        sl = float(f['low'])
        risk = px - sl
        if risk <= 0:
            continue
        tp = px + 1.8 * risk
        trade = {'entry_idx': i, 'entry': px, 'sl': sl, 'tp': tp, 'rr': 1.8, 'bars': 0}
        in_trade = True

    wins = [t for t in trades if t['pnl_r'] > 0]
    losses = [t for t in trades if t['pnl_r'] < 0]
    total = len(trades)
    win_rate = float(len(wins) / total) if total else 0.0
    pnl = [t['pnl_r'] for t in trades]
    avg_win = float(np.mean([p for p in pnl if p > 0])) if wins else 0.0
    avg_loss = float(np.mean([p for p in pnl if p < 0])) if losses else 0.0
    expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss
    eq = [INITIAL_EQUITY] + [INITIAL_EQUITY + sum(t['pnl_usd'] for t in trades[: idx + 1]) for idx in range(len(trades))]
    eq_arr = np.array(eq, dtype=float)
    peak = np.maximum.accumulate(eq_arr)
    max_dd = float(np.max((peak - eq_arr) / peak)) if peak.size else 0.0
    gross_profit = float(sum(t['pnl_usd'] for t in trades if t['pnl_usd'] > 0))
    gross_loss = float(abs(sum(t['pnl_usd'] for t in trades if t['pnl_usd'] < 0)))
    pf = gross_profit / gross_loss if gross_loss else float('inf')
    out = {
        'strategy_id': 'strategy_amd_po3_M15',
        'symbol': 'XAUUSD',
        'timeframe': 'M15',
        'total_trades': total,
        'win_rate': win_rate,
        'avg_win_r': avg_win,
        'avg_loss_r': avg_loss,
        'expectancy_r': round(float(expectancy), 6),
        'max_drawdown_pct': round(max_dd * 100, 4),
        'profit_factor': round(float(pf), 6),
        'equity_curve': [{'timestamp': int(pd.Timestamp(date[min(i, len(date) - 1)]).timestamp()), 'equity': round(float(e), 2)} for i, e in enumerate(eq)],
        'trades': trades[:80],
        'source': 'local_csv backtest',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('trades', total, 'win_rate', round(win_rate, 4), 'expectancy', round(float(expectancy), 4), 'max_dd', round(max_dd * 100, 2), 'pf', round(float(pf), 2))


if __name__ == '__main__':
    run()
