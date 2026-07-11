import os, sys, json
sys.path.insert(0, r'C:\Users\user\Desktop\hermes_claude\mt5draw_venv\Lib\site-packages')
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

TERMINAL = r'C:\Program Files\MetaTrader 5\terminal64.exe'
SYMBOL = 'XAUUSD'
TF_MAP = {'M15': mt5.TIMEFRAME_M15, 'H4': mt5.TIMEFRAME_H4}
WINDOWS = {'M15': 672, 'H4': 112}

def round_p(price, step):
	if not step: return float(price)
	return round(float(price)/step)*step

mt5.initialize(TERMINAL)
info = mt5.symbol_info(SYMBOL)
step = getattr(info, 'point', 0.01) or 0.01
end_ts = datetime.now().isoformat()+'Z'
dfs = {}
for label, tf in TF_MAP.items():
	data = mt5.copy_rates_from_pos(SYMBOL, tf, 0, WINDOWS[label])
	if data is None: raise RuntimeError(f"{label}: {mt5.last_error()}")
	dfs[label] = pd.DataFrame(data)

mt5.shutdown()
for df in dfs.values():
	df['time'] = pd.to_datetime(df['time'], unit='s', utc=True).dt.tz_convert(None)
	df.index = pd.to_datetime(df['time'])

out = {}

def detect_fvgs(df, step):
	rows = []
	for i in range(1, len(df)-1):
		r1, r2, r3 = df.iloc[i-1], df.iloc[i], df.iloc[i+1]
		if r2['high'] > r1['high'] and r3['low'] < r2['low']:
			bot = round_p(float(r3['low']), step); top = round_p(float(r1['high']), step)
			if top > bot: rows.append({'time': df.index[i+1].isoformat()+'Z', 'kind':'BEARISH_iFVG' if top-bot < 1.0 else 'BEARISH_FVG', 'bot':bot, 'top':top})
		if r2['low'] < r1['low'] and r3['high'] > r2['high']:
			bot = round_p(float(r1['low']), step); top = round_p(float(r3['high']), step)
			if top > bot: rows.append({'time': df.index[i+1].isoformat()+'Z', 'kind':'BULLISH_iFVG' if top-bot < 1.0 else 'BULLISH_FVG', 'bot':bot, 'top':top})
	return rows

def detect_structure(df):
	highs=df['high'].values; lows=df['low'].values
	sh,sl=[],[]
	for i in range(1,len(df)-1):
		if highs[i]>highs[i-1] and highs[i]>highs[i+1]: sh.append((df.index[i], float(highs[i])))
		if lows[i]<lows[i-1] and lows[i]<lows[i+1]: sl.append((df.index[i], float(lows[i])))
	ob=[]
	for i in range(3,len(df)):
		if lows[i-2] < lows[i-3] and lows[i-2] < lows[i-1]:
			ob.append({'time':df.index[i-2].isoformat()+'Z','type':'BUY','low':float(lows[i-2]),'high':float(lows[i-3]),'idx':i-2})
		if highs[i-2] > highs[i-3] and highs[i-2] > highs[i-1]:
			ob.append({'time':df.index[i-2].isoformat()+'Z','type':'SELL','low':float(highs[i-1]),'high':float(highs[i-2]),'idx':i-2})
	return sh,sl,ob

def detect_trendlines(sh, sl, per_kind=35):
	lines=[]
	def make(pts, ok):
		res=[]
		for i in range(len(pts)):
			for j in range(i+1, len(pts)):
				ta,pa=pts[i]; tb,pb=pts[j]
				if ta==tb: continue
				slope=(pb-pa)/((pd.Timestamp(tb)-pd.Timestamp(ta)).total_seconds() or 1e-9)
				if ok(slope): res.append((ta,pa,tb,pb))
		seen,uniq=set(),[]
		for x in res:
			k=(round(x[1],2),round(x[3],2)); 
			if k not in seen: seen.add(k); uniq.append(x)
		return uniq[:per_kind]
	lines += [{'kind':'descending','a_time':str(ta.isoformat())+'Z','a_price':round(pa,2),'b_time':str(tb.isoformat())+'Z','b_price':round(pb,2)} for ta,pa,tb,pb in make(sh, lambda s:-2_000_000<s<0)]
	lines += [{'kind':'ascending','a_time':str(ta.isoformat())+'Z','a_price':round(pa,2),'b_time':str(tb.isoformat())+'Z','b_price':round(pb,2)} for ta,pa,tb,pb in make(sl, lambda s:0<s<2_000_000)]
	return lines

def detect_confluence(ob, step):
	# Price clustering with 1-point buckets on rounded prices
	from collections import Counter
	buckets = Counter()
	for o in ob:
		hi = round_p(o['high'], step)
		buckets[hi] += 1
	# pick buckets with >=2
	out = []
	for price, cnt in buckets.items():
		if cnt >= 2:
			out.append({'time': '', 'low': price - step*3, 'high': price + step*3, 'type': ob[0]['type'], 'count': cnt})
	return out

def current_bias(df):
	closes=df['close'].values
	if len(closes)<20: return 'NEUTRAL'
	ma=pd.Series(closes).ewm(span=20,adjust=False).mean().values
	if closes[-1]>ma[-1]: return 'BULLISH'
	if closes[-1]<ma[-1]: return 'BEARISH'
	return 'NEUTRAL'

for label in ['M15','H4']:
	df = dfs[label]
	fvgs = detect_fvgs(df, step)
	sh, sl, ob = detect_structure(df)
	lines = detect_trendlines(sh, sl)
	confluence = detect_confluence(ob, step)
	b = current_bias(df)
	out[label] = {
		'timeframe': label,
		'start': df.index[0].isoformat()+'Z','end': end_ts,
		'bars': len(df), 'fvg_count': len(fvgs), 'ob_count': len(ob), 'trendline_count': len(lines), 'confluence_count': len(confluence),
		'current_bias': b,
		'setups': {
			'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
			'bias': b,
			'possible_setups': [
				{'name':'iFVG mitigate -> reversal','condition':'Re-enter rising OB or bullish iFVG + reclaim of broken BOS (bearish CHOCH)'},
				{'name':'Liquidity sweep + CHOCH reclaim','condition':'Wick below OB + close > prior swing high + CHOCH broken'},
				{'name':'HTF swing trendline rejection','condition':'Contact with swing trendline + directional close + liquidity return'},
				{'name':'PO3 AMD OB-FVG confluence','condition':'Weak 02 > CHOCH 01 > BOS obj + BUY OB align'}
			]
		},
		'fvgs': [{'time':r['time'],'kind':r['kind'],'bot':r['bot'],'top':r['top'],'range':round(r['top']-r['bot'],2)} for r in fvgs],
		'order_blocks': ob,
		'trendlines': lines,
		'confluences': confluence
	}

# save
for dst in [r'C:\Users\user\Desktop\hermes_claude\data\rnd\xau_smc_analysis.json',
            r'C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\xau_smc_data.json']:
	os.makedirs(os.path.dirname(dst), exist_ok=True)
	with open(dst,'w') as f: json.dump(out,f,indent=2,default=str)
	print('WROTE', dst)

# Sample summary
for k,v in out.items():
	print(k, 'bars=', v['bars'], 'fvg=', v['fvg_count'], 'ob=', v['ob_count'], 'trendlines=', v['trendline_count'], 'confluences=', v['confluence_count'], 'bias=', v['current_bias'])
