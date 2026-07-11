import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
import json

mt5.initialize()

now = datetime.now(timezone.utc)
tf_map = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
}

summary = {}
for tf, tf_const in tf_map.items():
    # Try to get last 500 bars
    rates = mt5.copy_rates_from("XAUUSD", tf_const, now, 500)
    if rates is None or len(rates) == 0:
        summary[tf] = {"bars": 0, "error": str(mt5.last_error())}
        continue
    bars = [{"time": int(r['time']), "open": float(r['open']), "high": float(r['high']),
             "low": float(r['low']), "close": float(r['close']), "volume": int(r['real_volume'])}
            for r in rates[-20:]]
    summary[tf] = {
        "bars_total": len(rates),
        "latest_time": datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc).isoformat(),
        "oldest_time": datetime.fromtimestamp(rates[0]['time'], tz=timezone.utc).isoformat(),
        "latest_close": float(rates[-1]['close']),
        "sample_bars_last": bars,
    }

print(json.dumps(summary, indent=2, default=str))
mt5.shutdown()
