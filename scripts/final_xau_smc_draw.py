import os, sys, json
sys.path.insert(0, r'C:\Users\user\Desktop\hermes_claude\mt5draw_venv\Lib\site-packages')
import MetaTrader5 as mt5
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

TERMINAL = r'C:\Program Files\MetaTrader 5\terminal64.exe'
SYMBOL = 'XAUUSD'
TF_ITEMS = [('M15', mt5.TIMEFRAME_M15, 700), ('H4', mt5.TIMEFRAME_H4, 120)]

def round_p(price, step):
	if not step: return float(price)
	return round(float(price)/step)*step

mt5.initialize(TERMINAL)
info = mt5.symbol_info(SYMBOL)
step = getattr(info, 'point', 0.01) or 0.01
end_ts = datetime.now().isoformat()+'Z'
dfs = {}

for label, tf, count in TF_ITEMS:
	data = mt5.copy_rates_from_pos(SYMBOL, tf, 0, count)
	if data is None:
		raise RuntimeError(f"{label}: copy_rates_from_pos failed: {mt5.last_error()}")
	df = pd.DataFrame(data)
	df['time'] = pd.to_datetime(df['time'], unit='s', utc=True).dt.tz_convert(None)
	df.index = pd.to_datetime(df['time'])
	dfs[label] = df
mt5.shutdown()

out = {}

def detect_fvgs(df):
	rows = []
	for i in range(1, len(df)-1):
		r1, r2, r3 = df.iloc[i-1], df.iloc[i], df.iloc[i+1]
		if r2['high'] > r1['high'] and r3['low'] < r2['low']:
			bot = round_p(float(r3['low']), step)
			top = round_p(float(r1['high']), step)
			if top > bot:
				rows.append({'time': df.index[i+1].isoformat()+'Z', 'kind':'BEARISH', 'bot':bot, 'top':top})
		if r2['low'] < r1['low'] and r3['high'] > r2['high']:
			bot = round_p(float(r1['low']), step)
			top = round_p(float(r3['high']), step)
			if top > bot:
				rows.append({'time': df.index[i+1].isoformat()+'Z', 'kind':'BULLISH', 'bot':bot, 'top':top})
	return rows

def detect_structure(df):
	highs=df['high'].values; lows=df['low'].values
	sh,sl=[],[]
	for i in range(1,len(df)-1):
		if highs[i]>highs[i-1] and highs[i]>highs[i+1]: sh.append((df.index[i].isoformat()+'Z', float(highs[i])))
		if lows[i]<lows[i-1] and lows[i]<lows[i+1]: sl.append((df.index[i].isoformat()+'Z', float(lows[i])))
	ob=[]
	for i in range(3,len(df)):
		if lows[i-2] < lows[i-3] and lows[i-2] < lows[i-1]:
			ob.append({'time':df.index[i-2].isoformat()+'Z','type':'BUY','low':float(lows[i-2]),'high':float(lows[i-3])})
		if highs[i-2] > highs[i-3] and highs[i-2] > highs[i-1]:
			ob.append({'time':df.index[i-2].isoformat()+'Z','type':'SELL','low':float(highs[i-1]),'high':float(highs[i-2])})
	return sh,sl,ob

def detect_trendlines(sh, sl, per_kind=55):
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
	lines += [{'kind':'descending','a_time':ta,'a_price':round(pa,2),'b_time':tb,'b_price':round(pb,2)} for ta,pa,tb,pb in make(sh,lambda s:-2_000_000<s<0)]
	lines += [{'kind':'ascending','a_time':ta,'a_price':round(pa,2),'b_time':tb,'b_price':round(pb,2)} for ta,pa,tb,pb in make(sl,lambda s:0<s<2_000_000)]
	return lines

def current_bias(df):
	closes=df['close'].values
	if len(closes)<20: return 'NEUTRAL'
	ma=pd.Series(closes).ewm(span=20,adjust=False).mean().values
	if closes[-1]>ma[-1]: return 'BULLISH'
	if closes[-1]<ma[-1]: return 'BEARISH'
	return 'NEUTRAL'

for label, _tf, _count in TF_ITEMS:
	df = dfs[label]
	fvgs = detect_fvgs(df)
	sh, sl, ob = detect_structure(df)
	lines = detect_trendlines(sh, sl)
	b = current_bias(df)
	out[label] = {
		'timeframe': label,
		'start': df.index[0].isoformat()+'Z','end': end_ts,
		'bars': len(df), 'fvg_count': len(fvgs), 'ob_count': len(ob), 'trendline_count': len(lines),
		'current_bias': b,
		'setups': {
			'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
			'bias': b,
			'possible_setups': [
				{'name':'iFVG mitigate -> reversal','condition':'Re-entry into FVG or OB + reclaim + stop-sweep beyond OB'},
				{'name':'Liquidity sweep + CHOCH reclaim','condition':'Wick below OB + close > prior swing high + CHOCH broken'},
				{'name':'HTF swing trendline rejection','condition':'Contact with swing trendline + directional close + liquidity return'},
				{'name':'PO3 AMD OB-FVG confluence','condition':'Weak 02 > CHOCH 01 > BOS obj + BUY OB align'}
			]
		},
		'fvgs': [{'time':r['time'],'kind':r['kind'],'bot':r['bot'],'top':r['top'],'range':round(r['top']-r['bot'],2)} for r in fvgs],
		'order_blocks': ob,
		'trendlines': lines
	}

out_path = r'C:\Users\user\Desktop\hermes_claude\data\rnd\xau_smc_analysis.json'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path,'w') as f: json.dump(out,f,indent=2,default=str)
print('WROTE', out_path)
for k,v in out.items():
	print(k, 'bars=', v['bars'], 'fvg=', v['fvg_count'], 'ob=', v['ob_count'], 'trendlines=', v['trendline_count'], 'bias=', v['current_bias'])

# draw
plt.rcParams['figure.dpi'] = 130
plt.rcParams['axes.facecolor'] = '#0d1117'
plt.rcParams['figure.facecolor'] = '#0d1117'
plt.rcParams['axes.edgecolor'] = '#1f2a34'
plt.rcParams['axes.labelcolor'] = '#c9d1d9'
plt.rcParams['xtick.color'] = '#c9d1d9'
plt.rcParams['ytick.color'] = '#c9d1d9'

FIG = r'C:\Users\user\Desktop\hermes_claude\data\rnd\xau_smc_charts.png'
fig, axes = plt.subplots(2, 1, figsize=(16,9))

for ax_i, (label, _tf, _count) in enumerate(TF_ITEMS):
	ax = axes[ax_i]
	df = dfs[label]
	ax.set_facecolor('#0d1117')
	ax.grid(color='#1f2a34', linewidth=.6)
	for sp in ax.spines.values(): sp.set_edgecolor('#1f2a34')
	ax.tick_params(labelsize=8, colors='#c9d1d9')
	tf_data = out[label]
	ax.set_title(f"XAUUSD  {label}   {tf_data['start'][:10]} -> {tf_data['end'][:10]}   Bias: {tf_data['current_bias']}   FVGs: {tf_data['fvg_count']}", color='#e6edf3', fontsize=10)
	for idx,row in df.iterrows():
		c = '#26a69a' if row['close']>=row['open'] else '#ef5350'
		ax.plot([idx,idx],[row['open'],row['close']],color=c,linewidth=3,solid_capstyle='butt')
		ax.plot([idx,idx],[row['high'],row['low']],color=c,linewidth=.8)
	for fvg in tf_data['fvgs']:
		t = pd.Timestamp(fvg['time'])
		is_bull = 'BULLISH' in fvg['kind'].upper()
		is_inv = 'IFVG' in fvg['kind'].upper()
		color = '#26a69a' if is_bull else '#ef5350'
		alpha = .28 if is_inv else .12
		lstyle = '-' if is_inv else '--'
		bot = float(fvg['bot']); top = float(fvg['top'])
		ax.axhspan(bot, top, xmin=0, xmax=1, facecolor=color, alpha=alpha)
		ax.axhline(bot, color=color, linestyle=lstyle, linewidth=.9, alpha=.75)
		ax.axhline(top, color=color, linestyle=lstyle, linewidth=.9, alpha=.75)
		ax.text(t, top, f"{fvg['kind']}\n{fvg['range']} pts", color=color, fontsize=7, va='bottom', ha='left', fontweight='bold')
	for ob in tf_data['order_blocks'][:20]:
		t = pd.Timestamp(ob['time'])
		c = '#4caf50' if ob['type']=='BUY' else '#f44336'
		ax.axhspan(float(ob['low']), float(ob['high']), xmin=0, xmax=1, facecolor=c, alpha=.10)
		ax.text(t, float(ob['high']), 'OB', color=c, fontsize=7, va='bottom')
	for ln in tf_data['trendlines'][:10]:
		ta = pd.Timestamp(ln['a_time']); tb = pd.Timestamp(ln['b_time'])
		c = '#29b6f6' if ln['kind']=='ascending' else '#ffa726'
		ax.plot([ta,tb],[float(ln['a_price']),float(ln['b_price'])],color=c,linewidth=1.2,linestyle='-.',alpha=.85)
	set_text = '\n'.join([f"{i+1}. {s['name']}" for i,s in enumerate(tf_data['setups']['possible_setups'][:3])])
	ax.text(.015,.98,set_text,transform=ax.transAxes,color='#e6edf3',va='top',ha='left',fontsize=8,
		bbox=dict(fc='#161b22',ec='#30363d',boxstyle='round,pad=.5',alpha=.92))
	ax.set_xlabel('Time', color='#c9d1d9')
	ax.set_ylabel('Price', color='#c9d1d9')
	ax.autoscale(enable=True, axis='both', tight=True)
fig.tight_layout(pad=1.0)
fig.savefig(FIG)
plt.close()
print('CHART', FIG)
