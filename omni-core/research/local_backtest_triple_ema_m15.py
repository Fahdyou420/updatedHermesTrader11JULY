"""Local triple EMA scalping backtester for XAUUSD M15."""
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

CSV_M15 = Path(r'C:/Users/user/Desktop/hermes_claude/data/market_data/local_xau_m15.csv')
OUT = Path(r'C:/Users/user/Desktop/hermes_claude/data/rnd/results/strategy_triple_ema_M15.json')
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


def ema(values, span):
    return pd.Series(values).ewm(span=span, adjust=False).mean().values


def run():
    data = load(CSV_M15)
    close = data['close']
    open_ = data['open']
    high = data['high']
    low = data['low']
    dt = data['date']
    n = len(close)
    ema50 = ema(close, 50)
    ema100 = ema(close, 100)
    ema150 = ema(close, 150)
    stoch_k = np.full(n, np.nan)
    stoch_d = np.full(n, np.nan)
    for i in range(4, n):
        hh = max(high[i - 4:i + 1])
        ll = min(low[i - 4:i + 1])
        denom = hh - ll
        raw = 0.0 if denom == 0 else (close[i] - ll) / denom * 100
        stoch_k[i] = raw
    for i in range(2, n):
        stoch_d[i] = np.nanmean(stoch_k[i - 2:i + 1])
    trades = []
    equity = INITIAL_EQUITY
    peak_equity = equity
    in_trade = False
    trade = None

    for i in range(160, n):
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
                if close_reason == 'sl':
                    pnl_r = -1.0
                    pnl_usd = -RISK_PCT * equity
                elif close_reason == 'tp':
                    pnl_r = float(trade['rr'])
                    pnl_usd = RISK_PCT * trade['rr'] * equity
                else:
                    denom = trade['entry'] - trade['sl']
                    pnl_r = ((px - trade['entry']) / denom) if denom else 0.0
                    pnl_usd = pnl_r * RISK_PCT * equity
                equity += pnl_usd
                trades.append(
                    {
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
                    }
                )
                in_trade = False
                trade = None
                if equity > peak_equity:
                    peak_equity = equity
            continue

        if not (ema50[i] > ema100[i] > ema150[i]):
            continue
        px = float(close[i])
        if not (float(low[i]) <= min(ema50[i], ema100[i]) <= px):
            continue
        stoch_recovering = stoch_k[i - 1] < 20 < stoch_k[i] if i and not np.isnan(stoch_k[i - 1]) and not np.isnan(stoch_k[i]) else False
        if not stoch_recovering:
            continue
        sl = float(min(low[i - 3: i + 1]))
        risk = px - sl
        if risk <= 0:
            continue
        tp = px + 2.0 * risk
        trade = {'entry_idx': i, 'entry': px, 'sl': sl, 'tp': tp, 'rr': 2.0, 'bars': 0}
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
        'strategy_id': 'strategy_triple_ema_M15',
        'symbol': 'XAUUSD',
        'timeframe': 'M15',
        'total_trades': total,
        'win_rate': win_rate,
        'avg_win_r': avg_win,
        'avg_loss_r': avg_loss,
        'expectancy_r': round(float(expectancy), 6),
        'max_drawdown_pct': round(max_dd * 100, 4),
        'profit_factor': round(float(pf), 6),
        'equity_curve': [{'timestamp': int(pd.Timestamp(dt[min(i, len(dt) - 1)]).timestamp()), 'equity': round(float(e), 2)} for i, e in enumerate(eq)],
        'trades': trades[:80],
        'source': 'local_csv backtest',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('trades', total, 'win_rate', round(win_rate, 4), 'expectancy', round(float(expectancy), 4), 'max_dd', round(max_dd * 100, 2), 'pf', round(float(pf), 2))


if __name__ == '__main__':
    run()
