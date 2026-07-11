import MetaTrader5 as mt5
from datetime import datetime, timezone
import json, math

mt5.initialize()
now = datetime.now(timezone.utc)

tf_map = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
}

def ema(closes, period):
    k = 2 / (period + 1)
    e = sum(closes[:period]) / period
    for c in closes[period:]:
        e = c * k + e * (1 - k)
    return e

def atr(highs, lows, closes, period=14):
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return sum(trs[-period:]) / period if len(trs) >= period else None

def pivots(bars, lookback=10):
    highs = [b['high'] for b in bars]
    lows = [b['low'] for b in bars]
    swing_highs = []
    swing_lows = []
    for i in range(lookback, len(bars)-lookback):
        if highs[i] == max(highs[i-lookback:i+lookback+1]):
            swing_highs.append((bars[i]['time'], highs[i]))
        if lows[i] == min(lows[i-lookback:i+lookback+1]):
            swing_lows.append((bars[i]['time'], lows[i]))
    return swing_highs, swing_lows

results = {}
for tf, tf_const in tf_map.items():
    rates = mt5.copy_rates_from("XAUUSD", tf_const, now, 500)
    if rates is None or len(rates) < 60:
        results[tf] = {"error": f"insufficient bars ({len(rates) if rates else 0})"}
        continue
    closes = [float(r['close']) for r in rates]
    highs = [float(r['high']) for r in rates]
    lows = [float(r['low']) for r in rates]
    latest_close = closes[-1]
    e20 = ema(closes, 20)
    e50 = ema(closes, 50)
    atr14 = atr(highs, lows, closes, 14)
    bias = "bullish" if latest_close > e20 > e50 else "bearish" if latest_close < e20 < e50 else "neutral"
    swing_highs, swing_lows = pivots(rates[-200:], lookback=3)
    nearest_resistance = min([h for t,h in swing_highs if h > latest_close], default=latest_close)
    nearest_support = max([l for t,l in swing_lows if l < latest_close], default=latest_close)
    results[tf] = {
        "close": round(latest_close, 2),
        "ema20": round(e20, 2),
        "ema50": round(e50, 2),
        "atr14": round(atr14, 2) if atr14 else None,
        "bias": bias,
        "nearest_resistance": round(nearest_resistance, 2),
        "nearest_support": round(nearest_support, 2),
        "dist_to_res": round(nearest_resistance - latest_close, 2),
        "dist_to_sup": round(latest_close - nearest_support, 2),
        "bars_range": f"{datetime.fromtimestamp(rates[0]['time'], tz=timezone.utc).strftime('%m-%d %H:%M')} to {datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc).strftime('%m-%d %H:%M')}",
    }

account = mt5.account_info()
positions = mt5.positions_get(symbol="XAUUSD")
result = {
    "native_rest_bridge": "DOWN (7779 refused)",
    "rpc_service": "UP (7778 OK)",
    "mt5_terminal": "UP (pid 1756)",
    "account": {
        "login": account.login,
        "server": account.server,
        "balance": round(account.balance, 2),
        "equity": round(account.equity, 2),
    },
    "open_positions": len(positions) if positions else 0,
    "scans": results,
}

print(json.dumps(result, indent=2, default=str))
mt5.shutdown()
