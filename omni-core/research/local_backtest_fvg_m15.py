"""Local SMC FVG fill backtester for XAUUSD M15."""
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

CSV_M15 = Path(r'C:/Users/user/Desktop/hermes_claude/data/market_data/local_xau_m15.csv')
CSV_H4 = Path(r'C:/Users/user/Desktop/hermes_claude/data/market_data/local_xau_h4.csv')
OUT = Path(r'C:/Users/user/Desktop/hermes_claude/data/rnd/results/local_smc_fvg_fill_M15.json')

INITIAL_EQUITY = 10000.0
RISK_PCT = 0.005


def load(path):
    df = pd.read_csv(path, sep='\t')
    df.columns = [c.strip() for c in df.columns]
    df['date'] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'], dayfirst=False)
    df = df.sort_values('date').reset_index(drop=True)
    return {
        'date': df['date'].values,
        'open': df['<OPEN>'].astype(float).values,
        'high': df['<HIGH>'].astype(float).values,
        'low': df['<LOW>'].astype(float).values,
        'close': df['<CLOSE>'].astype(float).values,
    }


def detect_fvgs(high, low, n, min_size=2.0):
    fvgs = []
    for i in range(2, n):
        if high[i-2] < low[i]:
            size = float(low[i] - high[i-2])
            if size >= min_size:
                fvgs.append({'idx': i, 'type': 'bullish', 'low': float(high[i-2]), 'high': float(low[i]), 'size': size})
        elif low[i-2] > high[i]:
            size = float(low[i-2] - high[i])
            if size >= min_size:
                fvgs.append({'idx': i, 'type': 'bearish', 'low': float(high[i]), 'high': float(low[i-2]), 'size': size})
    return fvgs


def swing_arrays(high, low, n, left=3, right=3):
    sh = []
    sl = []
    for i in range(left, n - right):
        if all(high[i] >= high[j] for j in range(i-left, i+right+1) if j != i):
            sh.append(i)
        if all(low[i] <= low[j] for j in range(i-left, i+right+1) if j != i):
            sl.append(i)
    return sh, sl


def run():
    m15 = load(CSV_M15)
    h4 = load(CSV_H4)
    n = min(len(m15['close']), 40000)
    start = len(m15['close']) - n
    o = m15['open'][start:]
    hh = m15['high'][start:]
    ll = m15['low'][start:]
    c = m15['close'][start:]
    dt = m15['date'][start:]
    h4c = list(h4['close'].astype(float))
    h4t = list(h4['date'])

    sh, slv = swing_arrays(hh, ll, n)
    # H4 aligned mean
    j = 0
    buf = []
    h4_mean = [float('nan')] * n
    for i in range(n):
        while j < len(h4t) and h4t[j] <= dt[i]:
            buf.append(float(h4c[j]))
            j += 1
        if buf:
            arr = buf[-50:] if len(buf) >= 50 else list(buf)
            h4_mean[i] = sum(arr) / len(arr)

    def bullish_bias(i):
        sh_i = [s for s in sh if s < i]
        sl_i = [s for s in slv if s < i]
        if len(sh_i) < 2 or len(sl_i) < 2:
            return False
        return bool(hh[sh_i[-1]] > hh[sh_i[-2]]) and bool(ll[sl_i[-1]] > ll[sl_i[-2]])

    fvg_index = detect_fvgs(hh, ll, n, min_size=2.0)
    fvg_ptr = 0
    active_fvgs = []

    trades = []
    equity = INITIAL_EQUITY
    peak = equity
    in_trade = False
    trade = None

    for i in range(60, n):
        if in_trade:
            trade['bars'] += 1
            hit_sl = bool(ll[i] <= trade['sl'])
            hit_tp = bool(hh[i] >= trade['tp'])
            close_reason = None
            if hit_sl and hit_tp:
                close_reason = 'sl' if abs(trade['sl'] - float(c[i])) < abs(trade['tp'] - float(c[i])) else 'tp'
            elif hit_sl:
                close_reason = 'sl'
            elif hit_tp:
                close_reason = 'tp'
            elif trade['bars'] >= 24:
                close_reason = 'timebar'
            if close_reason:
                px = float(c[i])
                if close_reason == 'sl':
                    pnl_r = -1.0
                    pnl_usd = -RISK_PCT * equity
                elif close_reason == 'tp':
                    pnl_r = trade['rr']
                    pnl_usd = RISK_PCT * trade['rr'] * equity
                else:
                    denom = trade['entry'] - trade['sl']
                    pnl_r = float((px - trade['entry']) / denom) if denom != 0 else 0.0
                    pnl_usd = pnl_r * RISK_PCT * equity
                equity += pnl_usd
                trades.append({
                    'entry_time': str(dt[trade['entry_idx']]),
                    'exit_time': str(dt[i]),
                    'direction': 'BUY',
                    'entry': float(trade['entry']),
                    'sl': float(trade['sl']),
                    'tp': float(trade['tp']),
                    'pnl_r': float(pnl_r),
                    'pnl_usd': float(pnl_usd),
                    'bars': trade['bars'],
                    'close_reason': close_reason,
                })
                in_trade = False
                trade = None
                if equity > peak:
                    peak = equity
            continue

        # update active FVGs
        while fvg_ptr < len(fvg_index) and fvg_index[fvg_ptr]['idx'] <= i:
            active_fvgs.append(fvg_index[fvg_ptr])
            fvg_ptr += 1
        # drop too old
        active_fvgs = [f for f in active_fvgs if (i - f['idx']) <= 200]

        if not bullish_bias(i):
            continue
        if j >= 1:
            if float(h4c[j-1]) <= h4_mean[i]:
                continue

        bull_fvgs = [f for f in active_fvgs if f['type'] == 'bullish' and 10 <= (i - f['idx']) <= 120]
        if not bull_fvgs:
            continue
        fvg = bull_fvgs[0]
        px = float(c[i])
        near = abs(px - fvg['high']) / fvg['high'] if fvg['high'] != 0 else 1.0
        bull = px > float(o[i]) and (float(hh[i]) != float(ll[i])) and (px - float(ll[i])) / (float(hh[i]) - float(ll[i])) > 0.55
        if near < 0.0015 and bull:
            sl = float(fvg['low']) - 1.0
            risk = px - sl
            if risk <= 0:
                continue
            tp = px + 1.8 * risk
            in_trade = True
            trade = {'entry_idx': i, 'entry': px, 'sl': sl, 'tp': tp, 'rr': 1.8, 'bars': 0}

    wins = [t for t in trades if t['pnl_r'] >= 0]
    losses = [t for t in trades if t['pnl_r'] < 0]
    total = len(trades)
    win_rate = len(wins) / total if total else 0.0
    avg_win_r = float(sum(t['pnl_r'] for t in wins)) / len(wins) if wins else 0.0
    avg_loss_r = float(sum(t['pnl_r'] for t in losses)) / len(losses) if losses else 0.0
    expectancy = win_rate * avg_win_r + (1 - win_rate) * avg_loss_r
    eq = [INITIAL_EQUITY]
    for t in trades:
        eq.append(eq[-1] + t['pnl_usd'])
    high = max(eq)
    max_dd = max((high - min(eq[k:])) / high for k in range(len(eq))) if eq else 0.0
    pf = abs(sum(t['pnl_usd'] for t in wins) / (sum(t['pnl_usd'] for t in losses) if losses else 1e-9))
    out = {
        'strategy_id': 'local_smc_fvg_fill_M15',
        'symbol': 'XAUUSD',
        'timeframe': 'M15',
        'total_trades': total,
        'win_rate': float(win_rate),
        'avg_win_r': float(avg_win_r),
        'avg_loss_r': float(avg_loss_r),
        'expectancy_r': float(expectancy),
        'max_drawdown_pct': float(max_dd * 100),
        'profit_factor': float(pf),
        'equity_curve': [{'timestamp': int(pd.Timestamp(dt[min(i, len(dt)-1)]).timestamp()), 'equity': round(float(e), 2)} for i, e in enumerate(eq)],
        'trades': trades[:80],
        'source': 'local_csv backtest',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding='utf-8')
    return out


if __name__ == '__main__':
    res = run()
    print('trades', res['total_trades'], 'win_rate', round(res['win_rate'],4), 'expectancy', round(res['expectancy_r'],4), 'max_dd', round(res['max_drawdown_pct'],2), 'pf', round(res['profit_factor'],2))
