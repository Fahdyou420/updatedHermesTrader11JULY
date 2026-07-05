"""Produce human-readable XAUUSD Mt5-closed-history review + strategy/backtest pack."""
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
for p in [RND, REPORTS, STRAT]:
    p.mkdir(parents=True, exist_ok=True)


def dt(ts):
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        return None


def load_deals():
    p = RND / 'xau_live_history_latest.json'
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_exit(d):
    c = (d.get('comment') or '')
    return bool(re.search(r'tp|sl', c, re.I))


def build_trades(deals):
    by_ticket = {}
    for d in deals:
        by_ticket.setdefault(d['ticket'], []).append(d)
    trades = []
    for ticket, rows in sorted(by_ticket.items()):
        rows.sort(key=lambda x: x.get('time', 0))
        entries = [x for x in rows if not is_exit(x)]
        exits = [x for x in rows if is_exit(x)]
        if not entries or not exits:
            continue
        o = entries[0]
        c = exits[-1]
        gross = float(c.get('profit', 0) or 0)
        commission = sum(float(x.get('commission', 0) or 0) for x in rows)
        swap = sum(float(x.get('swap', 0) or 0) for x in rows)
        net = gross + commission + swap
        trades.append({
            'ticket': ticket,
            'open_time': dt(o.get('time')),
            'close_time': dt(c.get('time')),
            'direction': 'BUY' if int(o.get('type', 0)) == 0 else 'SELL',
            'open_lots': float(o.get('lots', 0) or 0),
            'close_lots': float(c.get('lots', 0) or 0),
            'open_price': float(o.get('price', 0) or 0),
            'close_price': float(c.get('price', 0) or 0),
            'gross_profit': gross,
            'commission': commission,
            'swap': swap,
            'net_pnl': net,
            'outcome': 'tp' if 'tp' in (c.get('comment') or '').lower() else 'sl' if 'sl' in (c.get('comment') or '').lower() else 'close',
            'comment': c.get('comment', '') or o.get('comment', ''),
        })
    trades.sort(key=lambda x: x['open_time'] or datetime.min.replace(tzinfo=timezone.utc))
    return trades


def summaries(trades):
    closed = [t for t in trades if t['close_time'] is not None]
    net = sum(t['net_pnl'] for t in closed)
    wins = [t for t in closed if t['net_pnl'] > 0]
    losses = [t for t in closed if t['net_pnl'] <= 0]
    eq = np.cumsum([t['net_pnl'] for t in closed]) if closed else np.array([0.0])
    peak = np.maximum.accumulate(eq)
    return {
        'sessions': len(trades),
        'closed': len(closed),
        'total_net_pnl': float(net),
        'win_rate': len(wins) / len(closed) if closed else 0.0,
        'profit_factor': (sum(t['net_pnl'] for t in wins) / abs(sum(t['net_pnl'] for t in losses))) if losses and sum(t['net_pnl'] for t in losses) != 0 else float('inf'),
        'avg_win': sum(t['net_pnl'] for t in wins) / len(wins) if wins else 0.0,
        'avg_loss': sum(t['net_pnl'] for t in losses) / len(losses) if losses else 0.0,
        'max_drawdown': float(np.max(peak - eq)) if closed else 0.0,
    }


def build_daily_df(start='2020-01-01', end='2026-06-04'):
    ticker = yf.Ticker('GC=F')
    df = ticker.history(start=start, end=end, interval='1d', auto_adjust=False)
    df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
    df.index = pd.to_datetime(df.index, utc=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift(1)).abs(),
        (df['low'] - df['close'].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(14).mean()
    return df


def backtest_pullback(df: pd.DataFrame):
    w = df.copy()
    weekly_close = w['close'].resample('W-FRI').last().ffill()
    weekly_ema = weekly_close.ewm(span=20, adjust=False).mean()
    weekly_trend = np.where(w['close'] > weekly_ema.reindex(w.index, method='ffill'), 1, -1)
    w['weekly_bias'] = weekly_trend
    w['pullback_distance'] = (w['close'] - w['ema20']).abs()
    entry_signal = ((w['weekly_bias'] == 1) & (w['pullback_distance'] <= 0.1 * w['atr14'])).astype(bool)
    entry_signal = entry_signal.shift(1).fillna(False)
    trades = []
    in_pos = False
    entry_price = sl = tp = 0.0
    for i in range(len(w)):
        row = w.iloc[i]
        if not in_pos:
            if bool(entry_signal.iloc[i]):
                in_pos = True
                entry_price = float(row['open'])
                atr = float(row['atr14']) if not math.isnan(row['atr14']) else 0.0
                sl = entry_price - 1.0 * atr
                tp = entry_price + 2.0 * atr
        else:
            low = float(row['low'])
            high = float(row['high'])
            if low <= sl:
                trades.append({'pnl': sl - entry_price, 'outcome': 'sl'})
                in_pos = False
            elif high >= tp:
                trades.append({'pnl': tp - entry_price, 'outcome': 'tp'})
                in_pos = False
            elif i == len(w) - 1:
                trades.append({'pnl': float(row['close']) - entry_price, 'outcome': 'timeout'})
                in_pos = False
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    total_pnl = float(sum(t['pnl'] for t in trades))
    win_rate = len(wins) / len(trades) if trades else 0.0
    pf = (sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses))) if losses and sum(t['pnl'] for t in losses) != 0 else float('inf')
    return {
        'trades_count': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'profit_factor': pf,
        'avg_win': sum(t['pnl'] for t in wins) / len(wins) if wins else 0.0,
        'avg_loss': sum(t['pnl'] for t in losses) / len(losses) if losses else 0.0,
    }


def write_html(path: Path, live_summary, backtest, sessions):
    rows = ''
    for t in sessions:
        rows += f"<tr><td>{t['ticket']}</td><td>{t['open_time']}</td><td>{t['close_time']}</td><td>{t['direction']}</td><td>{t['open_lots']:.2f}</td><td>{t['open_price']:.2f}</td><td>{t['close_price']:.2f}</td><td>{t['net_pnl']:.2f}</td><td>{t['comment']}</td></tr>"
    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Hermes XAUUSD Strategy Report</title>
<style>body{{font-family:Arial,sans-serif;margin:20px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #cdd3db;padding:6px 8px;font-size:13px}}th{{background:#f4f7fb}}</style></head><body>
<h1>Hermes XAUUSD strategy report</h1>
<h2>Live history summary</h2>
<ul>
<li>closed trades: {live_summary['closed']}</li>
<li>total net PnL: {live_summary['total_net_pnl']:.2f}</li>
<li>win rate: {live_summary['win_rate']:.2%}</li>
<li>profit factor: {live_summary['profit_factor']:.2f}</li>
</ul>
<h2>2020-2026 backtest summary</h2>
<ul>
<li>trades: {backtest['trades_count']}</li>
<li>win rate: {backtest['win_rate']:.2%}</li>
<li>total PnL units: {backtest['total_pnl']:.2f}</li>
<li>profit factor: {backtest['profit_factor']:.2f}</li>
</ul>
<h2>Trades</h2>
<table><thead><tr><th>Ticket</th><th>Open</th><th>Close</th><th>Dir</th><th>Lots</th><th>Open</th><th>Close</th><th>Net PnL</th><th>Comment</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>"""
    path.write_text(html, encoding='utf-8')


def main():
    deals = load_deals()
    trades = build_trades(deals)
    live_summary = summaries(trades)
    df = build_daily_df()
    backtest = backtest_pullback(df)
    # artifacts
    with open(RND / 'xau_closed_trades_latest.json', 'w', encoding='utf-8') as f:
        json.dump({'summary': live_summary, 'trades': [{
            **t,
            'open_time': t['open_time'].isoformat() if isinstance(t['open_time'], datetime) else str(t['open_time']),
            'close_time': t['close_time'].isoformat() if isinstance(t['close_time'], datetime) else str(t['close_time']),
        } for t in trades]}, f, indent=2)
    with open(RND / 'xau_backtest_pullback_2020-2026.json', 'w', encoding='utf-8') as f:
        json.dump(backtest, f, indent=2)
    strat_text = """CONFIG = dict(
    strategy_name='gold_nbc_pullback_v2',
    instrument='XAUUSD',
    base_lot=0.01,
    sl_atr_mult=1.0,
    tp_atr_mult=2.0,
    weekly_bias_required=True,
    confluence='OB/FVG/atr-volume-expansion',
)"""
    (STRAT / 'gold_nbc_pullback_v2.py').write_text(strat_text, encoding='utf-8')
    write_html(REPORTS / 'xau_strategy_report.html', live_summary, backtest, trades)
    print('done')
    print(json.dumps({'live': live_summary, 'backtest': backtest}, indent=2))


if __name__ == '__main__':
    main()
