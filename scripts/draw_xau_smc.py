import os, sys, json, math
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

REQUESTED = {
    'XAUUSD': {'M15': 15, 'H4': 240},
}

SYMBOL = 'XAUUSD'
TIMEFRAMES = {'M15': 15, 'H4': 240}
COLORS = {
    'bullish_fvg': 'clrGreen',
    'bearish_fvg': 'clrRed',
    'inverted_bullish_fvg': 'clrSpringGreen',
    'inverted_bearish_fvg': 'clrCrimson',
    'setup': 'clrBlueViolet',
    'trend': 'clrDodgerBlue',
}

# Refresh symbol info cache
mt5.symbol_select(SYMBOL, True)

symbol_info = mt5.symbol_info(SYMBOL)
if symbol_info is None:
    sys.exit(f"Symbol {SYMBOL} not found")

tick_size = getattr(symbol_info, 'pt', getattr(symbol_info, 'point', 0.01))
digits = getattr(symbol_info, 'digits', 2)
step = getattr(symbol_info, 'point', 0.01)
print(f'symbol={SYMBOL} digits={digits} step={step}')


def round_price(value: float) -> float:
    return round(value / step) * step


def fetch(name, timeframe):
    today = datetime.now()
    start = today - timedelta(days=35)
    data = mt5.copy_rates_from(name, timeframe, start, 0)
    if data is None:
        raise RuntimeError(f"copy_rates_from failed for {name} {timeframe}")
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True).dt.tz_localize(None)
    df.index = pd.to_datetime(df['time'])
    return df


def candle_fvg(r1, r2, r3):
    if r2['high'] >= r1['high'] or r2['low'] <= r3['low']:
        return None
    top = round_price((r1['high'] + r3['high']) / 2.0)
    bot = round_price((r1['low'] + r3['low']) / 2.0)
    if top <= bot:
        top = round_price(r1['high'])
        bot = round_price(r3['low'])
    if top <= bot:
        return None
    return bot, top


def detect_fvgs(df):
    records = df.to_records()
    gaps = []
    for i in range(1, len(records) - 1):
        r1 = records[i - 1]
        r2 = records[i]
        r3 = records[i + 1]
        if r2['high'] > r1['high'] and r3['low'] < r2['low']:
            print(f'  BULLISH FVG candidate row={r2["time"]} r={r2["high"]-r3["low"]:.2f}')
        elif r2['low'] < r1['low'] and r3['high'] > r2['high']:
            print(f'  BEARISH FVG candidate row={r2["time"]} r={r3["high"]-r2["low"]:.2f}')
    return gaps


def stairs(df, lookback=40):
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    swing_highs, swing_lows = [], []
    for idx in range(1, len(df) - 1):
        if highs[idx] > highs[idx - 1] and highs[idx] > highs[idx + 1]:
            swing_highs.append((df.index[idx], highs[idx]))
        if lows[idx] < lows[idx - 1] and lows[idx] < lows[idx + 1]:
            swing_lows.append((df.index[idx], lows[idx]))
    return swing_highs, swing_lows


def detect_trendlines(swing_highs, swing_lows, max_slope=2_000_000):
    lines = []
    for kind, swings in [('ascending', swing_lows), ('descending', swing_highs)]:
        for i in range(len(swings)):
            for j in range(i + 1, len(swings)):
                t0, p0 = swings[i]
                t1, p1 = swings[j]
                if t0 == t1:
                    continue
                slope = (p1 - p0) / ((t1 - t0).total_seconds() or 1e-9)
                if kind == 'ascending' and slope > 0 and slope < max_slope:
                    lines.append((t0, p0, t1, p1, slope))
                elif kind == 'descending' and slope < 0 and slope > -max_slope:
                    lines.append((t0, p0, t1, p1, slope))
    seen = set()
    uniq = []
    for line in lines:
        key = (round_price(line[1]), round_price(line[3]), round(line[4], 9))
        if key not in seen:
            seen.add(key)
            uniq.append(line)
    return uniq


def draw_rect_obj(name, price1, price2, yfrom, yto, color, fill, style=0, width=1):
    mt5.ObjectCreate(name, mt5.OBJ_RECTANGLE, 0, yfrom, price1, yto, price2)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_COLOR, color)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_STYLE, style)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_WIDTH, width)
    if fill:
        mt5.ObjectSetInteger(0, name, mt5.OBJPROP_FILL, True)


def draw_label(name, price, time, text, color, font_size=8):
    mt5.ObjectCreate(name, mt5.OBJ_TEXT, 0, time, price)
    mt5.ObjectSetString(0, name, mt5.OBJPROP_TEXT, text)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_COLOR, color)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_FONTSIZE, font_size)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_BACK, False)


def draw_trendline(name, t0, p0, t1, p1, color, width=1, style=0):
    mt5.ObjectCreate(name, mt5.OBJ_TRENDLINE, 0, t0, p0, t1, p1)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_COLOR, color)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_WIDTH, width)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_STYLE, style)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_RAY, False)
    mt5.ObjectSetInteger(0, name, mt5.OBJPROP_BACK, True)


# init terminal
terminal = r'C:\Program Files\MetaTrader 5\terminal64.exe'
if not mt5.initialize(path=terminal):
    print(f"MT5 init failed {mt5.last_error()}")
    sys.exit(1)

results = {}
for tf_label, tf in TIMEFRAMES.items():
    print(f'=== {tf_label} ===')
    df = fetch(SYMBOL, tf)
    df = df.tail(1000)
    print(f'bars={len(df)} window={df.index[0]} -> {df.index[-1]}')
    detect_fvgs(df)
    swings = stairs(df)
    print(f'swing_highs={len(swings[0])} swing_lows={len(swings[1])}')
    lines = detect_trendlines(*swings)
    print(f'trendline_candidates={len(lines)}')
    results[tf_label] = {'bars': len(df), 'swing_highs': len(swings[0]), 'swing_lows': len(swings[1]), 'lines': len(lines)}

mt5.shutdown()
print(json.dumps(results, indent=2, default=str))
