import MetaTrader5 as mt5
from datetime import datetime, timezone
import json

mt5.initialize()
account = mt5.account_info()
positions = mt5.positions_get(symbol="XAUUSD")
history = mt5.history_deals_get(datetime(2026, 7, 4, tzinfo=timezone.utc), datetime.now(timezone.utc))

result = {
    "account": {
        "login": account.login,
        "server": account.server,
        "balance": account.balance,
        "equity": account.equity,
        "trade_mode": account.trade_mode,
        "trade_allowed": account.trade_allowed,
        "currency": account.currency,
    },
    "open_positions": [],
    "history_deals_count": len(history) if history else 0,
}

if positions:
    for p in positions:
        result["open_positions"].append({
            "ticket": p.ticket,
            "symbol": p.symbol,
            "type": int(p.type),
            "volume": p.volume,
            "price_open": p.price_open,
            "price_current": p.price_current,
            "sl": p.sl,
            "tp": p.tp,
            "profit": p.profit,
            "comment": p.comment,
            "time": int(p.time),
        })

print(json.dumps(result, indent=2, default=str))
mt5.shutdown()
