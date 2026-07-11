"""Local SMC OB entry backtester for XAUUSD M15."""
import json, math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

CSV_M15 = Path(r'C:/Users/user/Desktop/hermes_claude/data/market_data/local_xau_m15.csv')
CSV_H4 = Path(r'C:/Users/user/Desktop/hermes_claude/data/market_data/local_xau_h4.csv')
OUT = Path(r'C:/Users/user/Desktop/hermes_claude/data/rnd/results/local_smc_ob_entry_M15.json')

INITIAL_EQUITY = 10000.0
RISK_PCT = 0.005


def load_array(path):
    df = pd.read_csv(path, sep='\t')
    df.columns = [c.strip() for c in df.columns]
    df['date'] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'], dayfirst=False)
    df = df.sort_values('date').reset_index(drop=True)
    arr = {
        'date': df['date'].values,
        'open': df['<OPEN>'].astype(float).values,
        'high': df['<HIGH>'].astype(float).values,
        'low': df['<LOW>'].astype(float).values,
        'close': df['<CLOSE>'].astype(float).values,
    }
    return arr


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
    m15 = load_array(CSV_M15)
    h4 = load_array(CSV_H4)
    n = min(len(m15['close']), 40000)
    start = len(m15['close']) - n
    o = m15['open'][start:]
    h = m15['high'][start:]
    l = m15['low'][start:]
    c = m15['close'][start:]
    dt = m15['date'][start:]
    h4c = list(h4['close'].astype(float))
    h4t = list(h4['date'])

    sh, sl_val = swing_arrays(h, l, n)

    idx4 = 0
    buf = []
    h4_mean = [float('nan')] * n
    for i in range(n):
        while idx4 < len(h4t) and h4t[idx4] <= dt[i]:
            buf.append(float(h4c[idx4]))
            idx4 += 1
        if buf:
            arr = buf[-50:] if len(buf) >= 50 else list(buf)
            h4_mean[i] = sum(arr) / len(arr)

    trades = []
    equity = INITIAL_EQUITY
    peak_equity = equity
    in_trade = False
    trade = None

    for i in range(60, n):
        if in_trade:
            trade['bars'] += 1
            hit_sl = bool(l[i] <= trade['sl'])
            hit_tp = bool(h[i] >= trade['tp'])
            close_reason = None
            if hit_sl and hit_tp:
                close_reason = 'sl' if abs(trade['sl'] - float(c[i])) < abs(trade['tp'] - float(c[i])) else 'tp'
            elif hit_sl:
                close_reason = 'sl'
            elif hit_tp:
                close_reason = 'tp'
            elif trade['bars'] >= 48:
                close_reason = 'timebar'

            if close_reason:
                px = float(c[i])
                if close_reason == 'sl':
                    pnl_r = -1.0
                    pnl_usd = -RISK_PCT * equity
                elif close_reason == 'tp':
                    pnl_r = float(trade['rr'])
                    pnl_usd = RISK_PCT * float(trade['rr']) * equity
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
                if equity > peak_equity:
                    peak_equity = equity
            continue

        sh_i = [s for s in sh if s < i]
        sl_i = [s for s in sl_val if s < i]
        if len(sh_i) < 2 or len(sl_i) < 2:
            continue
        if not (bool(h[sh_i[-1]] > h[sh_i[-2]]) and bool(l[sl_i[-1]] > l[sl_i[-2]])):
            continue
        if idx4 >= 1:
            if float(h4c[idx4-1]) <= h4_mean[i]:
                continue

        ob_idx = None
        for s in reversed(sl_i):
            if s == 0:
                break
            if bool(c[s-1] < o[s-1]):
                ob_idx = s-1
                break
        if ob_idx is None:
            continue

        ob_high = float(h[ob_idx])
        ob_low = float(l[ob_idx])
        entry = float(c[i])
        sl = ob_low
        risk = entry - sl
        if risk <= 0:
            continue
        tp = entry + 2.0 * risk
        near = abs(entry - ob_high) / ob_high if ob_high != 0 else 1.0
        bull = bool(entry > float(o[i])) and (float(h[i]) != float(l[i])) and ((entry - float(l[i])) / (float(h[i]) - float(l[i])) > 0.55)
        if near < 0.0015 and bull:
            in_trade = True
            trade = {'entry_idx': i, 'entry': entry, 'sl': sl, 'tp': tp, 'rr': 2.0, 'bars': 0}

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
        'strategy_id': 'local_smc_ob_entry_M15',
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
