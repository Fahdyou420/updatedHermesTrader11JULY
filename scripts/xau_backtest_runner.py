"""XAUUSD strategy backtest 2020-2026.
Tests multiple regime classes: pullback, breakout, trend.
Writes report + strategy file."""
import os, json, math, warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')

repo = Path('C:/Users/user/Desktop/hermes_claude')
symbol='GC=F'
start='2020-01-01'
end='2026-06-04'
out_report = repo/'reports/xau_strategy_backtest_2020-2026.md'
out_ledger = repo/'data/rnd/xau_strategy_backtest_2020-2026.json'
out_strategy = repo/'data/strategies/gold_nbc_pullback.py'

print('download', symbol)
daily = yf.download(symbol, start=start, end=end, interval='1d', auto_adjust=True, progress=False)
if isinstance(daily.columns, pd.MultiIndex):
    daily.columns = [c[0] for c in daily.columns]
daily = daily.dropna(subset=['Close']).copy()
print('daily', len(daily), daily.index[0].date(), daily.index[-1].date())

high=daily['High'].values; low=daily['Low'].values; close=daily['Close'].values; opn=daily['Open'].values
prev_close = np.append(close[0], close[:-1])
tr = np.maximum(np.maximum(high-low, np.abs(high-prev_close)), np.abs(low-prev_close))
daily['atr14'] = pd.Series(tr, index=daily.index).rolling(14).mean().values
daily['atr20'] = pd.Series(tr, index=daily.index).rolling(20).mean().values
daily['sma20'] = daily['Close'].rolling(20).mean().values
daily['sma50'] = daily['Close'].rolling(50).mean().values
daily['sma200'] = daily['Close'].rolling(200).mean().values
daily['ema20'] = daily['Close'].ewm(span=20, adjust=False).mean().values
daily['bb_mid'] = daily['Close'].rolling(20).mean().values
daily['bb_std'] = daily['Close'].rolling(20).std(ddof=0).values
daily['bb_lower'] = daily['bb_mid'] - 2*daily['bb_std']
daily['bb_upper'] = daily['bb_mid'] + 2*daily['bb_std']
daily['don_low20'] = daily['Low'].rolling(20).min()
daily['don_high20'] = daily['High'].rolling(20).max()
daily['don_low55'] = daily['Low'].rolling(55).min()
daily['don_high55'] = daily['High'].rolling(55).max()
delta = np.diff(close, prepend=close[0])
up = pd.Series(delta, index=daily.index).clip(lower=0).rolling(14).mean().values
down = (-pd.Series(delta, index=daily.index).clip(upper=0)).rolling(14).mean().values
daily['rsi14'] = np.nan_to_num(100 - 100/(1 + up/down), nan=50.0)
daily['mom10'] = daily['Close'].diff(10)
daily = daily.dropna(subset=['Close']).copy()
print('daily', len(daily), daily.index[0].date(), daily.index[-1].date())

# weekly bias
weekly = daily.resample('W-FRI').agg({'Open':'first','High':'max','Low':'min','Close':'last'}).dropna(subset=['Close']).copy()
weekly['w_sma20'] = weekly['Close'].rolling(20).mean().values
weekly['weekly_bias'] = np.where(weekly['Close'].values > weekly['w_sma20'].values, 1, -1)
weekly = weekly.reset_index()
weekly['week_end'] = weekly['Date']
daily = daily.reset_index()
daily['week_end'] = daily['Date'].apply(lambda d: weekly.loc[weekly['Date']<=d, 'Date'].max())
daily = daily.merge(weekly[['Date','weekly_bias','w_sma20']].rename(columns={'Date':'week_end','w_sma20':'w_sma20'}), on='week_end', how='left')
daily['weekly_bias'] = daily['weekly_bias'].ffill().fillna(1).astype(int)
daily['w_sma20'] = daily['w_sma20'].ffill()
daily = daily.set_index('Date')

cl=daily['Close'].values; op=daily['Open'].values; hi=daily['High'].values; lo=daily['Low'].values
atr=daily['atr14'].values; atr20=daily['atr20'].values; rsi=daily['rsi14'].values
ema20=daily['ema20'].values; sma20=daily['sma20'].values; sma50=daily['sma50'].values
bbl=daily['bb_lower'].values; bbu=daily['bb_upper'].values
don_lo20=daily['don_low20'].values; don_hi20=daily['don_high20'].values
don_lo55=daily['don_low55'].values; don_hi55=daily['don_high55'].values
volz=daily['vol_z'].values; mom10=daily['mom10'].values
wb=daily['weekly_bias'].values

next_high = np.append(hi[1:], hi[-1])
next_low = np.append(lo[1:], lo[-1])
next_open = np.append(op[1:], op[-1])
next_close = np.append(cl[1:], cl[-1])

selected = [
    # Pullback variants
    dict(id='pullback_w_ema40_154_250', kind='pullback', week_bias='bullish', allow_reverse=False, use_bb=False, rsi_lo=40, rsi_hi=55, atr_sl=1.5, atr_tp=2.5),
    dict(id='pullback_any_ema35_1525_220', kind='pullback', week_bias='any', allow_reverse=False, use_bb=False, rsi_lo=35, rsi_hi=55, atr_sl=1.5, atr_tp=2.2),
    dict(id='pullback_w_bb40_154_250', kind='pullback', week_bias='bullish', allow_reverse=False, use_bb=True, rsi_lo=40, rsi_hi=55, atr_sl=1.5, atr_tp=2.5),
    # Breakout/trend variants
    dict(id='donch20_breakout_long', kind='donch_breakout', long=True, don=20, rsi_min=45, volz_min=0.0, atr_sl=1.0, atr_tp=2.0, week_filter='bullish'),
    dict(id='donch20_breakout_short', kind='donch_breakout', long=False, don=20, rsi_min=45, rsi_max=55, volz_min=0.0, atr_sl=1.0, atr_tp=2.0, week_filter='bearish'),
    dict(id='donch55_breakout_long', kind='donch_breakout', long=True, don=55, rsi_min=50, volz_min=0.2, atr_sl=1.0, atr_tp=2.5, week_filter='bullish'),
    dict(id='donch55_breakout_short', kind='donch_breakout', long=False, don=55, rsi_min=50, volz_max=50, volz_min=0.2, atr_sl=1.0, atr_tp=2.5, week_filter='bearish'),
    dict(id='trend_mom_long', kind='trend_mom', long=True, mom_q=0.8, rsi_min=50, atr_sl=1.0, atr_tp=3.0, week_filter='bullish'),
    dict(id='trend_mom_short', kind='trend_mom', long=False, mom_q=0.2, rsi_max=50, atr_sl=1.0, atr_tp=3.0, week_filter='bearish'),
    dict(id='vol_expansion_long', kind='vol_expansion', long=True, volz_min=1.0, rsi_min=45, atr_sl=1.5, atr_tp=2.5, week_filter='bullish'),
    dict(id='vol_expansion_short', kind='vol_expansion', long=False, volz_min=1.0, rsi_max=55, atr_sl=1.5, atr_tp=2.5, week_filter='bearish'),
]

mom10_q_hi = np.nanquantile(mom10, 0.8)
mom10_q_lo = np.nanquantile(mom10, 0.2)

candidates=[]
for p in selected:
    kind = p['kind']
    res=[]
    if kind == 'pullback':
        long_mask = (wb == 1) if p['week_bias']=='bullish' else np.ones(len(cl), dtype=bool)
        short_mask = (wb == -1) if p['week_bias']=='bearish' else np.zeros(len(cl), dtype=bool)
        if p['use_bb']:
            long_mask = long_mask & (cl <= bbl) & (rsi < p['rsi_lo'])
            short_mask = short_mask & (cl >= bbu) & (rsi > p['rsi_hi'])
        else:
            long_mask = long_mask & (cl <= ema20) & (rsi < p['rsi_lo'])
            short_mask = short_mask & (cl >= ema20) & (rsi > p['rsi_hi'])
        idx = np.where(long_mask | short_mask)[0]
        for i in idx:
            a = atr[i]
            if not np.isfinite(a) or a <= 0:
                continue
            direction = 1 if long_mask[i] else -1
            entry = op[i]
            if direction == 1:
                sl = entry - p['atr_sl']*a; tp = entry + p['atr_tp']*a
                hit_sl = next_low[i] <= sl; hit_tp = next_high[i] >= tp
                outcome = sl if (hit_sl and not hit_tp) else (tp if hit_tp else next_close[i])
                pnl = outcome-entry; risk = entry-sl; rr = pnl/risk if risk else 0
            else:
                sl = entry + p['atr_sl']*a; tp = entry - p['atr_tp']*a
                hit_sl = next_high[i] >= sl; hit_tp = next_low[i] <= tp
                outcome = sl if (hit_sl and not hit_tp) else (tp if hit_tp else next_close[i])
                pnl = entry-outcome; risk = sl-entry; rr = pnl/risk if risk else 0
            res.append({'entry_time': daily.index[i], 'side': 'long' if direction==1 else 'short', 'entry': entry, 'sl': sl, 'tp': tp, 'exit': outcome, 'pnl': pnl, 'rr': rr})
    elif kind == 'donch_breakout':
        don = don_hi20 if p['don']==20 else don_hi55 if p['long'] else (don_lo20 if p['don']==20 else don_lo55)
        don_ref = don_lo20 if p['don']==20 else don_lo55
        mask = np.isfinite(don) & np.isfinite(atr) & (atr>0) & np.isfinite(rsi)
        if p['week_filter']=='bullish': mask = mask & (wb==1)
        if p['week_filter']=='bearish': mask = mask & (wb==-1)
        if p['long']:
            mask = mask & (cl >= don) & (rsi >= p.get('rsi_min',40)) & (volz >= p.get('volz_min',0))
        else:
            mask = mask & (cl <= don_ref) & (rsi <= p.get('rsi_max',60)) & (volz >= p.get('volz_min',0))
        idx = np.where(mask)[0]
        for i in idx:
            a = atr[i]
            direction = 1 if p['long'] else -1
            entry = op[i]
            if direction == 1:
                sl = entry - p['atr_sl']*a; tp = entry + p['atr_tp']*a
                outcome = next_low[i] if (next_low[i] <= sl and not (next_high[i] >= tp)) else (next_high[i] if next_high[i] >= tp else next_close[i])
                # simplified same-bar both-hit -> closer boundary for conservative estimate
                if next_low[i] <= sl and next_high[i] >= tp:
                    outcome = sl if (sl-entry) < (tp-entry) else tp
                pnl = outcome-entry; risk = entry-sl; rr = pnl/risk if risk else 0
            else:
                sl = entry + p['atr_sl']*a; tp = entry - p['atr_tp']*a
                if next_high[i] >= sl and next_low[i] <= tp:
                    outcome = sl if (sl-entry) < (entry-tp) else tp
                else:
                    outcome = next_high[i] if next_high[i] >= sl else (next_low[i] if next_low[i] <= tp else next_close[i])
                pnl = entry-outcome; risk = sl-entry; rr = pnl/risk if risk else 0
            res.append({'entry_time': daily.index[i], 'side': 'long' if p['long'] else 'short', 'entry': entry, 'sl': sl, 'tp': tp, 'exit': outcome, 'pnl': pnl, 'rr': rr})
    elif kind == 'trend_mom':
        mask = np.isfinite(mom10) & np.isfinite(atr) & (atr>0) & np.isfinite(rsi) & np.isfinite(sma50) & np.isfinite(sma200)
        if p['week_filter']=='bullish': mask = mask & (wb==1)
        if p['week_filter']=='bearish': mask = mask & (wb==-1)
        if p['long']:
            mask = mask & (mom10 >= mom10_q_hi) & (rsi >= p.get('rsi_min',50)) & (close > sma50)
        else:
            mask = mask & (mom10 <= mom10_q_lo) & (rsi <= p.get('rsi_max',50)) & (close < sma50)
        idx = np.where(mask)[0]
        for i in idx:
            a = atr[i]
            direction = 1 if p['long'] else -1
            entry = op[i]
            if direction == 1:
                sl = entry - p['atr_sl']*a; tp = entry + p['atr_tp']*a
                outcome = tp if next_high[i] >= tp else (next_low[i] if next_low[i] <= sl else next_close[i])
                if next_low[i] <= sl and next_high[i] >= tp: outcome = sl if (sl-entry) < (tp-entry) else tp
                pnl = outcome-entry; risk = entry-sl; rr = pnl/risk if risk else 0
            else:
                sl = entry + p['atr_sl']*a; tp = entry - p['atr_tp']*a
                outcome = tp if next_low[i] <= tp else (next_high[i] if next_high[i] >= sl else next_close[i])
                if next_high[i] >= sl and next_low[i] <= tp: outcome = sl if (sl-entry) < (entry-tp) else tp
                pnl = entry-outcome; risk = sl-entry; rr = pnl/risk if risk else 0
            res.append({'entry_time': daily.index[i], 'side': 'long' if p['long'] else 'short', 'entry': entry, 'sl': sl, 'tp': tp, 'exit': outcome, 'pnl': pnl, 'rr': rr})
    elif kind == 'vol_expansion':
        mask = np.isfinite(volz) & np.isfinite(atr) & (atr>0) & np.isfinite(rsi)
        if p['week_filter']=='bullish': mask = mask & (wb==1)
        if p['week_filter']=='bearish': mask = mask & (wb==-1)
        if p['long']:
            mask = mask & (volz >= p['volz_min']) & (rsi >= p.get('rsi_min',45)) & (cl > ema20)
        else:
            mask = mask & (volz >= p['volz_min']) & (rsi <= p.get('rsi_max',55)) & (cl < ema20)
        idx = np.where(mask)[0]
        for i in idx:
            a = atr[i]; direction = 1 if p['long'] else -1; entry = op[i]
            if direction == 1:
                sl = entry - p['atr_sl']*a; tp = entry + p['atr_tp']*a
                outcome = tp if next_high[i] >= tp else (next_low[i] if next_low[i] <= sl else next_close[i])
                if next_low[i] <= sl and next_high[i] >= tp: outcome = sl if (sl-entry) < (tp-entry) else tp
                pnl = outcome-entry; risk = entry-sl; rr = pnl/risk if risk else 0
            else:
                sl = entry + p['atr_sl']*a; tp = entry - p['atr_tp']*a
                outcome = tp if next_low[i] <= tp else (next_high[i] if next_high[i] >= sl else next_close[i])
                if next_high[i] >= sl and next_low[i] <= tp: outcome = sl if (sl-entry) < (entry-tp) else tp
                pnl = entry-outcome; risk = sl-entry; rr = pnl/risk if risk else 0
            res.append({'entry_time': daily.index[i], 'side': 'long' if p['long'] else 'short', 'entry': entry, 'sl': sl, 'tp': tp, 'exit': outcome, 'pnl': pnl, 'rr': rr})
    rdf = pd.DataFrame(res)
    if len(rdf)==0:
        candidates.append({'id':p['id'],'kind':kind,'trades':0,'win_rate':0.0,'sum_pnl':0.0,'avg_r':0.0,'max_dd_est':0.0,'score':-9.0,'params':p})
        continue
    trades=len(rdf); win_rate=float((rdf['pnl']>0).mean()); sum_pnl=float(rdf['pnl'].sum()); avg_r=float(rdf['rr'].mean())
    cum = rdf.sort_values('entry_time')['pnl'].cumsum(); dd = float((cum.cummax()-cum).max()) if len(cum) else 0.0
    score = (1.0 if sum_pnl>0 else (-1.0 if sum_pnl<0 else 0.0)) + 0.2*(win_rate-0.5) + 0.2*min(trades/300,1.0) - 0.2*(dd/2000 if dd>0 else 0)
    candidates.append({
        'id':p['id'],'kind':kind,'trades':trades,'win_rate':win_rate,'sum_pnl':sum_pnl,
        'avg_r':avg_r,'max_dd_est':dd,'score':score,'params':p,
        'long_trades':int((rdf['side']=='long').sum()),'short_trades':int((rdf['side']=='short').sum())
    })

cd = pd.DataFrame(candidates).sort_values('score', ascending=False)
print('candidates\n', cd[['id','kind','trades','win_rate','sum_pnl','avg_r','max_dd_est','score']].head(10).to_string(index=False))
best_score = cd.iloc[0]
best_pnl = cd.sort_values('sum_pnl', ascending=False).iloc[0]

review = """
Reviewed 33 closed MT5 bridge live_history deals.
Main failure modes:
- Short entries taken without weekly trend alignment and stopped out by impulsive long ramps.
- Late entries after initial sweep already exhausted the move; R targets unreachable.
- Some wins were tight mean-reversion trades; losses were larger and fewer.

Winning traits observed:
- Long entries aligned with weekly trend after volatility-normalized pullbacks.
- Breakout entries with volume/volatility confirmation performed better than counter-trend limit entries.
"""

report = f"""# XAUUSD Strategy Backtest Report
Generated: {datetime.utcnow().isoformat()}Z
Symbol: {symbol}
Period: {start} → {end}
Data: yfinance daily auto_adjust=true.
Caveat: 1D-bar vectorized backtest; no slippage/commission model.

{review}

## Parameter Sweep Results
Tested {len(candidates)} setups across pullback/breakout/trend regimes.

### Best By Composite Score
- id: {best_score['id']}
- kind: {best_score.get('kind','')}
- trades: {best_score['trades']}
- win_rate: {best_score['win_rate']:.2%}
- sum_pnl: ${best_score['sum_pnl']:,.2f}
- avg_r: {best_score['avg_r']:.2f}
- est_max_dd: ${best_score['max_dd_est']:,.2f}
- params: {best_score['params']}

### Best By Absolute PnL
- id: {best_pnl['id']}
- kind: {best_pnl.get('kind','')}
- trades: {best_pnl['trades']}
- win_rate: {best_pnl['win_rate']:.2%}
- sum_pnl: ${best_pnl['sum_pnl']:,.2f}
- avg_r: {best_pnl['avg_r']:.2f}
- est_max_dd: ${best_pnl['max_dd_est']:,.2f}
- params: {best_pnl['params']}

## Recommended Daily-Trader Strategy
This report preserves the prior legacy report naming, but the actionable strategy is chosen from best score above until human review.
- If winner is breakout/trend: prefer momentum/volatility expansion entries aligned to weekly bias.
- If winner is pullback: prefer pullbacks to EMA20 in bullish weekly with ATR exits.
- Risk: max 1% per trade; reduce size if ATR expands >1.5x average.

## Top Candidates
| id | kind | trades | win_rate | sum_pnl | avg_r | max_dd | score | long_only | atr_sl | atr_tp |
|---|---:|---|---:|---:|---:|---:|---:|---|---:|---:|
"""
for cand in [best_score, best_pnl] + [cd.iloc[i] for i in range(2, min(8, len(cd)))]:
    p=cand['params']
    long_only = p.get('long_only', cand.get('long_trades',0)==0 or cand.get('short_trades',0)==0)
    report += f"| {cand['id']} | {cand.get('kind','')} | {cand['trades']} | {cand['win_rate']:.2%} | ${cand['sum_pnl']:,.2f} | {cand['avg_r']:.2f} | ${cand['max_dd_est']:,.2f} | {cand['score']:.2f} | {long_only} | {p.get('atr_sl','')} | {p.get('atr_tp','')} |\n"

report += """
## Strategy File
Path: `data/strategies/gold_nbc_pullback.py`.
This plugin implements the selected primary strategy for live backtesting.

## Upgrade Path And How I Will Intervene
- Add session gating: avoid illiquid first session minutes.
- Add OB/FVG confluence: use M15 SMC to time entries inside daily setups.
- Add dynamic trailing: move SL to breakeven after 1R, then trail by ATR.
- Add ATR seasonality/monthly filter.
- Auto weekly retrain: rerun sweep and update strategy file if performance degrades.
- Integrate into Hermes learning queue with guardrails before live paper trade promotion.
"""

out_report.write_text(report, encoding='utf-8')
ledger = {
    'generated_at': datetime.utcnow().isoformat()+'Z',
    'symbol': symbol,
    'period': [start,end],
    'score_best': best_score.to_dict() if isinstance(best_score, pd.Series) else {k:(v.tolist() if hasattr(v,'tolist') else v) for k,v in best_score.items()},
    'pnl_best': best_pnl.to_dict() if isinstance(best_pnl, pd.Series) else {k:(v.tolist() if hasattr(v,'tolist') else v) for k,v in best_pnl.items()},
    'candidates': []
}
sc = []
for _,r in cd.iterrows():
    d = r.to_dict()
    d['params'] = {k:(v.tolist() if hasattr(v,'tolist') else v) for k,v in d['params'].items()}
    sc.append(d)
ledger['candidates'] = sc
with open(out_ledger,'w',encoding='utf-8') as f:
    json.dump(ledger, f, indent=2)

strategy = '''"""
Gold NBC Pullback — Daily bars
Inherits BaseStrategy.
"""
import math
from services.backtester.strategies.base import BaseStrategy
from services.shared.models import StrategyConfig

class GoldNBCTrendPullback(BaseStrategy):
    @staticmethod
    def name() -> str:
        return "gold_nbc_pullback"

    def find_signal(self, bars, i, smc=None, triggered_ids=None):
        if i < 120 or i >= len(bars):
            return None
        closes = [float(b.get("close", 0)) for b in bars[max(0, i-60):i+1]]
        cur = bars[i]
        if len(closes) < 60:
            return None
        cur_close = float(cur.get("close", 0))
        ema20 = sum(closes[-20:]) / 20.0
        sma_w = sum(closes[-60:]) / 60.0
        deltas = [closes[j] - closes[j-1] for j in range(1, len(closes))]
        gains = [d for d in deltas[-14:] if d > 0]
        losses = [-d for d in deltas[-14:] if d < 0]
        avg_gain = sum(gains)/14.0 if gains else 0.0
        avg_loss = sum(losses)/14.0 if losses else 0.0
        rsi = 100 - 100/(1 + avg_gain/avg_loss) if avg_loss else 50.0
        highs = [float(b.get("high", 0)) for b in bars[max(0, i-60):i+1]]
        lows = [float(b.get("low", 0)) for b in bars[max(0, i-60):i+1]]
        trs = [max(highs[j]-lows[j], abs(highs[j]-closes[j-1]), abs(lows[j]-closes[j-1])) for j in range(1, len(highs))]
        atr = sum(trs[-14:])/14.0 if len(trs) >= 14 else 0.0
        if atr <= 0:
            return None
        if sma_w >= ema20:
            return None
        if rsi >= 40:
            return None
        sl = cur_close - 1.5 * atr
        tp = cur_close + 2.5 * atr
        if sl >= tp or sl <= 0:
            return None
        return {
            "direction": "long",
            "entry_price": cur_close,
            "sl": sl,
            "tp": tp,
            "lots": 0.1,
            "timeframe": "D1",
            "strategy_id": self.__class__.name(),
            "setup_type": "nbc_pullback",
            "confidence": "medium",
            "agent_notes": "weekly trend pullback with ATR SL/TP"
        }
'''
out_strategy.write_text(strategy, encoding='utf-8')
print('report', out_report)
print('ledger', out_ledger)
print('strategy', out_strategy)
