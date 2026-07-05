"""Native-only probe + M15/D1 backtest pack from 7779."""
from __future__ import annotations

import json, math, re
from pathlib import Path

import numpy as np
import pandas as pd
import requests

REPO = Path('C:/Users/user/Desktop/hermes_claude')
RND = REPO / 'data' / 'rnd'
REPORTS = REPO / 'reports'
RND.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

BASE='http://localhost:7779/api/native'
now_iso=pd.Timestamp.now(tz='UTC').isoformat()

account=requests.get(f'{BASE}/account', timeout=20).json()
positions=requests.get(f'{BASE}/positions', timeout=20).json()
history=requests.get(f'{BASE}/history', params={'days':30,'instrument':'XAUUSD'}, timeout=20).json()
m15_bars=requests.get(f'{BASE}/latest_bars', params={'instrument':'XAUUSD','tf':'M15','n':7000}, timeout=60).json()
d1_bars=requests.get(f'{BASE}/latest_bars', params={'instrument':'XAUUSD','tf':'D1','n':8000}, timeout=60).json()

for name, data in {
    'native_account_snapshot_7779.json': account,
    'native_positions_snapshot_7779.json': positions,
    'native_history_30d_xauusd.json': history,
    'native_m15_bars_2024_2026.json': m15_bars,
    'native_d1_bars_2020_2026.json': d1_bars,
}.items():
    with open(RND / name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# paired closed trades from raw history
trades = history.get('trades', []) or []
by_pos: dict = {}
for t in trades:
    pid = t.get('position_id')
    by_pos.setdefault(pid, []).append(t)
paired = []
for pid, rows in by_pos.items():
    rows.sort(key=lambda x: x.get('time', 0) or 0)
    entry = next((x for x in rows if x.get('entry') == 0), None)
    close = next((x for x in rows if x.get('entry') == 1), None)
    if entry and close:
        paired.append({
            'position_id': pid,
            'ticket': entry.get('ticket') or close.get('ticket'),
            'type': 'BUY' if entry.get('type') == 0 else 'SELL',
            'open_time': entry.get('time'),
            'close_time': close.get('time'),
            'volume': float(entry.get('volume') or 0),
            'open_price': float(entry.get('price') or 0),
            'close_price': float(close.get('price') or 0),
            'gross_profit': float(close.get('profit') or 0),
            'commission': float(close.get('commission') or 0) + float(entry.get('commission') or 0),
            'swap': float(close.get('swap') or 0) + float(entry.get('swap') or 0),
            'net_pnl': float(close.get('profit') or 0) + float(close.get('commission') or 0) + float(close.get('swap') or 0),
            'comment': str(close.get('comment', '') or entry.get('comment', '') or ''),
        })
paired.sort(key=lambda x: x['open_time'] if x['open_time'] is not None else 0)
with open(RND / 'xau_native_closed_trades_latest.json', 'w', encoding='utf-8') as f:
    json.dump(paired, f, indent=2)

closed=[t for t in paired if t['open_time'] is not None and t['close_time'] is not None]
net=sum(t['net_pnl'] for t in closed)
gross=sum(t['gross_profit'] for t in closed)
commission=sum(t['commission'] for t in closed)
swap=sum(t['swap'] for t in closed)
wins=[t for t in closed if t['net_pnl']>0]
losses=[t for t in closed if t['net_pnl']<=0]
win_rate=len(wins)/len(closed) if closed else 0.0
pf=(sum(t['net_pnl'] for t in wins)/abs(sum(t['net_pnl'] for t in losses))) if losses and sum(t['net_pnl'] for t in losses) != 0 else float('inf')
avg_win=sum(t['net_pnl'] for t in wins)/len(wins) if wins else 0.0
avg_loss=sum(t['net_pnl'] for t in losses)/len(losses) if losses else 0.0
max_win=max((t['net_pnl'] for t in wins), default=0.0)
max_loss=min((t['net_pnl'] for t in losses), default=0.0)
if closed and len(closed) > 1:
    peak = np.maximum.accumulate(np.cumsum([t['net_pnl'] for t in closed]))
    max_dd = float(np.max(peak - np.cumsum([t['net_pnl'] for t in closed])))
else:
    max_dd=0.0

comments=[t['comment'] for t in closed if t['comment']]
sl=sum(1 for c in comments if re.search(r'\[?sl', c, re.I))
tp=sum(1 for c in comments if re.search(r'\[?tp', c, re.I))
short_losses=[t for t in closed if t['type']=='SELL' and t['net_pnl']<0]
big_loss=[t for t in closed if t['net_pnl']<-1000]
failure={'comments': len(comments), 'sl_tagged': sl, 'tp_count': tp, 'short_losses': len(short_losses), 'big_loss_trades': len(big_loss)}

def bars_df(bars):
    rows=[]
    for b in bars:
        rows.append({'time': pd.Timestamp(int(b['time']), unit='s', tz='UTC'), 'open': float(b['open']), 'high': float(b['high']), 'low': float(b['low']), 'close': float(b['close']), 'volume': float(b.get('tick_volume', 0) or 0)})
    df=pd.DataFrame(rows).set_index('time').sort_index()
    return df

m15_df = bars_df(m15_bars)
d1_df = bars_df(d1_bars)
m15_1h = m15_df.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().copy()

# M15 derived features on compressed 1H basis
m15_1h['ema20'] = m15_1h['close'].ewm(span=20, adjust=False).mean()
m15_1h['high20'] = m15_1h['high'].rolling(20).max().shift(1)
m15_1h['atr14'] = pd.concat([m15_1h['high']-m15_1h['low'],(m15_1h['high']-m15_1h['close'].shift(1)).abs(),(m15_1h['low']-m15_1h['close'].shift(1)).abs()], axis=1).max(axis=1).rolling(14).mean()
weekly_close_m15 = m15_1h['close'].resample('W-FRI').last().ffill()
w_ema_m15 = weekly_close_m15.ewm(span=20, adjust=False).mean()
m15_1h['weekly_bias'] = np.where(m15_1h['close'] > w_ema_m15.reindex(m15_1h.index, method='ffill'), 1, -1)
m15_1h = m15_1h.dropna(subset=['ema20','high20','atr14','weekly_bias']).copy()

cost = 0.30
in_pos=False
entry=sl=tp=0.0
entry_idx=0
m15_trades=[]
for i in range(len(m15_1h)):
    row=m15_1h.iloc[i]
    if not in_pos:
        breakout=bool(row['close'] > row['high20'])
        weekly_bull=bool(row['weekly_bias']==1)
        if breakout and weekly_bull:
            in_pos=True
            entry=float(row['open'])
            sl=float(row['high20']) - 0.5*float(row['atr14'])
            tp=entry + 2.0*float(row['atr14'])
            entry_idx=i
    else:
        high=float(row['high']); low=float(row['low'])
        if low <= sl:
            m15_trades.append({'pnl': sl-entry-cost, 'outcome': 'sl', 'len': i-entry_idx+1})
            in_pos=False
        elif high >= tp:
            m15_trades.append({'pnl': tp-entry-cost, 'outcome': 'tp', 'len': i-entry_idx+1})
            in_pos=False
        elif i == len(m15_1h)-1:
            m15_trades.append({'pnl': float(row['close'])-entry-cost, 'outcome': 'timeout', 'len': i-entry_idx+1})
            in_pos=False

def summary_metrics(trades):
    if not trades:
        return {'trades':0,'win_rate':0.0,'total_pnl':0.0,'profit_factor':0.0,'avg_win':0.0,'avg_loss':0.0,'avg_len':0.0}
    pnl=[t['pnl'] for t in trades]
    wins=[p for p in pnl if p>0]; losses=[p for p in pnl if p<=0]
    return {
        'trades': len(trades),
        'win_rate': len(wins)/len(trades),
        'total_pnl': float(np.sum(pnl)),
        'profit_factor': (float(np.sum(wins))/abs(float(np.sum(losses)))) if losses and float(np.sum(losses)) != 0 else float('inf'),
        'avg_win': float(np.mean(wins)) if wins else 0.0,
        'avg_loss': float(np.mean(losses)) if losses else 0.0,
        'avg_len': float(np.mean([t['len'] for t in trades])),
    }

# D1 native backtest 2020-2026
d1_analysis = d1_df.copy()
d1_analysis['ema20'] = d1_analysis['close'].ewm(span=20, adjust=False).mean()
d1_analysis['high20'] = d1_analysis['high'].rolling(20).max().shift(1)
weekly_close_d1 = d1_analysis['close'].resample('W-FRI').last().ffill()
w_ema_d1 = weekly_close_d1.ewm(span=20, adjust=False).mean()
d1_analysis['weekly_bias'] = np.where(d1_analysis['close'] > w_ema_d1.reindex(d1_analysis.index, method='ffill'), 1, -1)
d1_analysis['atr14'] = pd.concat([d1_analysis['high']-d1_analysis['low'],(d1_analysis['high']-d1_analysis['close'].shift(1)).abs(),(d1_analysis['low']-d1_analysis['close'].shift(1)).abs()], axis=1).max(axis=1).rolling(14).mean()
d1_analysis=d1_analysis.dropna(subset=['ema20','high20','weekly_bias','atr14']).copy()
start_2020=pd.Timestamp('2020-01-01', tz='UTC')
end_2026=pd.Timestamp('2026-06-04', tz='UTC')
d1_analysis=d1_analysis.loc[(d1_analysis.index >= start_2020) & (d1_analysis.index < end_2026)].copy()

in_pos=False
entry=sl=tp=0.0
entry_idx=0
d1_trades=[]
for i in range(len(d1_analysis)):
    row=d1_analysis.iloc[i]
    if not in_pos:
        breakout=bool(row['close'] > row['high20'])
        weekly_bull=bool(row['weekly_bias']==1)
        if breakout and weekly_bull:
            in_pos=True
            entry=float(row['open'])
            sl=float(row['high20']) - 0.5*float(row['atr14'])
            tp=entry + 2.0*float(row['atr14'])
            entry_idx=i
    else:
        high=float(row['high']); low=float(row['low'])
        if low <= sl:
            d1_trades.append({'pnl': sl-entry-cost, 'outcome': 'sl', 'len': i-entry_idx+1})
            in_pos=False
        elif high >= tp:
            d1_trades.append({'pnl': tp-entry-cost, 'outcome': 'tp', 'len': i-entry_idx+1})
            in_pos=False
        elif i == len(d1_analysis)-1:
            d1_trades.append({'pnl': float(row['close'])-entry-cost, 'outcome': 'timeout', 'len': i-entry_idx+1})
            in_pos=False

m15_backtest=summary_metrics(m15_trades)
d1_backtest=summary_metrics(d1_trades)

metrics={
    'generated': now_iso,
    'native_source': BASE,
    'live_history_summary': {
        'paired_closed': len(closed),
        'net_pnl': float(net),
        'gross': float(gross),
        'commission': float(commission),
        'swap': float(swap),
        'win_rate': float(win_rate),
        'profit_factor': float(pf),
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
        'max_win': float(max_win),
        'max_loss': float(max_loss),
        'max_drawdown': float(max_dd),
        'failures': failure,
    },
    'm15_backtest_recent': m15_backtest,
    'd1_backtest_native_2020_2026': d1_backtest,
    'selected': 'BREAKOUT',
    'source_files': {
        'm15_bars': 'data/rnd/native_m15_bars_2024_2026.json',
        'd1_bars': 'data/rnd/native_d1_bars_2020_2026.json',
        'closed_trades': 'data/rnd/xau_native_closed_trades_latest.json',
    }
}
with open(RND / 'xau_native_backtest_matrix_m15_d1.json', 'w', encoding='utf-8') as f:
    json.dump(metrics, f, indent=2)

report = f"""# XAUUSD Native MT5 Native-Only Report
Generated: {now_iso}
Endpoints: {BASE}

## Live Account State
Login: {account.get('login')} | Server: {account.get('server')} | Balance: {account.get('balance')} | Equity: {account.get('equity')} | Margin: {account.get('margin')} | Free Margin: {account.get('margin_free')} | Pos: {positions.get('total')}
Account: {account.get('name')}

## Native Paired History Review
- closed trades: {len(closed)}
- total net PnL: {float(net):.2f}
- gross: {float(gross):.2f} | commission: {float(commission):.2f} | swap: {float(swap):.2f}
- win rate: {float(win_rate):.2%}
- profit factor: {float(pf):.2f}
- avg win: {float(avg_win):.2f} | avg loss: {float(avg_loss):.2f}
- max win: {float(max_win):.2f} | max loss: {float(max_loss):.2f}
- estimated max drawdown: {float(max_dd):.2f}
- failures: {json.dumps(failure)}

## Recent M15 Backtest Results
- trades: {m15_backtest['trades']}
- win rate: {m15_backtest['win_rate']:.2%}
- PnL: {m15_backtest['total_pnl']:.2f}
- PF: {m15_backtest['profit_factor']:.2f}
- avg win: {m15_backtest['avg_win']:.2f} | avg loss: {m15_backtest['avg_loss']:.2f}

## Long-Horizon D1 Backtest Results 2020-01-01 -> 2026-06-03
- trades: {d1_backtest['trades']}
- win rate: {d1_backtest['win_rate']:.2%}
- PnL: {d1_backtest['total_pnl']:.2f}
- PF: {d1_backtest['profit_factor']:.2f}
- avg win: {d1_backtest['avg_win']:.2f} | avg loss: {d1_backtest['avg_loss']:.2f}

## Strategy / Improvements
- Drop counter-trend shorts unless weekly D1 breaks bearish structure
- Trailing ATR after TP1; move SL to breakeven earlier
- Add volume confirmation and market-phase filter
- ATR-based lot sizing at 0.5% risk
- Preferred timeframe: D1; M15 valid for proxy/coverage
"""
(REPORTS / 'xau_native_strategy_report.md').write_text(report, encoding='utf-8')
print('done')
print(json.dumps(metrics, indent=2))
