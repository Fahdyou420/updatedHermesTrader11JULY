import os, sys, json
sys.path.insert(0, r'C:\Users\user\Desktop\hermes_claude\mt5draw_venv\Lib\site-packages')
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

SYMBOL = 'XAUUSD'
tf_map = {'M15': 15, 'H4': 240}
window_bars = {'M15': 672, 'H4': 120}
TERMINAL = r'C:\Program Files\MetaTrader 5\terminal64.exe'


def round_price(value, step):
    if step <= 0:
        return float(value)
    return round(value / step) * step


def fetch(name, timeframe, count):
    data = mt5.copy_rates_from_pos(name, timeframe, 0, count)
    if data is None:
        raise RuntimeError(f"copy_rates_from_pos failed: {mt5.last_error()}")
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True).dt.tz_convert(None)
    df.index = pd.to_datetime(df['time'])
    return df


def detect_structure(df):
    highs = df['high'].values
    lows = df['low'].values
    swing_highs, swing_lows = [], []
    for i in range(1, len(df) - 1):
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            swing_highs.append((i, df.index[i], float(highs[i])))
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            swing_lows.append((i, df.index[i], float(lows[i])))
    ob_zones = []
    for i in range(3, len(df)):
        if lows[i - 2] < lows[i - 3] and lows[i - 2] < lows[i - 1]:
            ob_zones.append({'idx': i - 2, 'time': str(df.index[i - 2].isoformat()), 'type': 'BUY', 'low': float(lows[i - 2]), 'high': float(lows[i - 3])})
        if highs[i - 2] > highs[i - 3] and highs[i - 2] > highs[i - 1]:
            ob_zones.append({'idx': i - 2, 'time': str(df.index[i - 2].isoformat()), 'type': 'SELL', 'low': float(highs[i - 1]), 'high': float(highs[i - 2])})
    return swing_highs, swing_lows, ob_zones


def detect_fvgs(df, step):
    gaps = []
    for i in range(1, len(df) - 1):
        r1, r2, r3 = df.iloc[i - 1], df.iloc[i], df.iloc[i + 1]
        # Bearish big FVG candidate: R2 high > R1 high, R3 low < R2 low
        if r2['high'] > r1['high'] and r3['low'] < r2['low']:
            top = round_price(float(r1['high']), step)
            bot = round_price(float(r3['low']), step)
            if top > bot:
                gaps.append({
                    'row_idx_after': i + 1, 'time': str(df.index[i + 1].isoformat()),
                    'ctx_idx': i, 'ctx_time': str(df.index[i].isoformat()),
                    'bot': round(bot, 2), 'top': round(top, 2), 'kind': 'BEARISH',
                    'range': round(top - bot, 2)
                })
        # Bullish big FVG candidate: R2 low < R1 low, R3 high > R2 high
        if r2['low'] < r1['low'] and r3['high'] > r2['high']:
            bot = round_price(float(r1['low']), step)
            top = round_price(float(r3['high']), step)
            if top > bot:
                gaps.append({
                    'row_idx_after': i + 1, 'time': str(df.index[i + 1].isoformat()),
                    'ctx_idx': i, 'ctx_time': str(df.index[i].isoformat()),
                    'bot': round(bot, 2), 'top': round(top, 2), 'kind': 'BULLISH',
                    'range': round(top - bot, 2)
                })
    # newest first
    gaps.reverse()
    return gaps


def detect_trendlines(swing_highs, swing_lows, max_candidates=120):
    uniq = []
    # descending lines through swing highs
    for i in range(len(swing_highs)):
        for j in range(i + 1, len(swing_highs)):
            t_i, p_i = swing_highs[i][1], swing_highs[i][2]
            t_j, p_j = swing_highs[j][1], swing_highs[j][2]
            if t_i == t_j:
                continue
            slope = (p_j - p_i) / ((t_j - t_i).total_seconds() or 1e-9)
            if -2_000_000 < slope < 0:
                uniq.append({'a_time': str(t_i.isoformat()), 'a_price': float(p_i), 'b_time': str(t_j.isoformat()), 'b_price': float(p_j), 'slope': float(slope), 'kind': 'descending'})
    # ascending lines through swing lows
    for i in range(len(swing_lows)):
        for j in range(i + 1, len(swing_lows)):
            t_i, p_i = swing_lows[i][1], swing_lows[i][2]
            t_j, p_j = swing_lows[j][1], swing_lows[j][2]
            if t_i == t_j:
                continue
            slope = (p_j - p_i) / ((t_j - t_i).total_seconds() or 1e-9)
            if 0 < slope < 2_000_000:
                uniq.append({'a_time': str(t_i.isoformat()), 'a_price': float(p_i), 'b_time': str(t_j.isoformat()), 'b_price': float(p_j), 'slope': float(slope), 'kind': 'ascending'})
    seen = set()
    filtered = []
    for line in uniq:
        key = (round(line['a_price'], 2), round(line['b_price'], 2), round(line['slope'], 12))
        if key not in seen:
            seen.add(key)
            filtered.append(line)
    return filtered[:max_candidates]


def heuristic_setups(df):
    closes = df['close'].values
    bias = 'NEUTRAL'
    if len(closes) >= 30:
        ma = pd.Series(closes).ewm(span=20, adjust=False).mean().values
        bias = 'BULLISH' if closes[-1] > ma[-1] else 'BEARISH' if closes[-1] < ma[-1] else 'NEUTRAL'
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    return {
        'analysis_time': ts,
        'bias': bias,
        'possible_setups': [
            {'name': 'FVG Fill / iFVG mitigate -> reversed', 'condition': 'HTL aligned mitigation + wick Shapiro + re-break'},
            {'name': 'Liquidity sweep + BOS reclaim', 'condition': 'Sweep below OB + close above HH inside PD array'},
            {'name': 'Swing trendline reject', 'condition': 'HTF swing TL touch with full wick in HTF direction'},
            {'name': 'HTF PO3 AMD entry', 'condition': 'OD/ON/OE buildup into key OB + 3 b/c BOS'}
        ]
    }


mt5.initialize(TERMINAL)
meta = mt5.symbol_info(SYMBOL)
step = getattr(meta, 'point', 0.01)
end_ts = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
out = {}
for label, tf in tf_map.items():
    count = window_bars[label]
    df = fetch(SYMBOL, tf, count)
    start_ts = df.index[0].isoformat()
    swings = detect_structure(df)
    fvgs = detect_fvgs(df, step)
    lines = detect_trendlines(*swings[:2])
    setups = heuristic_setups(df)
    out[label] = {
        'timeframe': label,
        'start': start_ts, 'end': end_ts,
        'bars': len(df), 'swing_highs': len(swings[0]), 'swing_lows': len(swings[1]),
        'ob_count': len(swings[2]), 'fvg_count': len(fvgs),
        'trendline_count': len(lines),
        'current_bias': setups['bias'],
        'setups': setups,
        'fvgs': fvgs,
        'trendlines': lines,
        'order_blocks': swings[2]
    }
mt5.shutdown()
out_path = r'C:\Users\user\Desktop\hermes_claude\data\rnd\xau_smc_analysis.json'
with open(out_path, 'w') as f:
    json.dump(out, f, indent=2, default=str)
print('WROTE', out_path)
print(json.dumps({k: {'bars': v['bars'], 'fvg_count': v['fvg_count'], 'ob_count': v['ob_count'], 'current_bias': v['current_bias']} for k, v in out.items()}, indent=2))
