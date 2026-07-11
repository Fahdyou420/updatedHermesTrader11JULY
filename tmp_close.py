import MetaTrader5 as mt5
import json
mt5.initialize(path=r"C:\Program Files\MetaTrader 5	erminal64.exe")
pos = mt5.positions_get()
print(json.dumps({'total': len(pos) if pos else 0, 'positions': [p._asdict() for p in (pos or [])]}, default=str))
for p in (pos or []):
    typ = mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY
    price = mt5.symbol_info_tick(p.symbol).bid if p.type == 0 else mt5.symbol_info_tick(p.symbol).ask
    if price is None:
        print('no tick', p.symbol)
        continue
    req = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': p.symbol,
        'volume': p.volume,
        'type': typ,
        'position': p.ticket,
        'price': price,
        'deviation': 20,
        'magic': 123456,
        'comment': 'close_' + str(p.ticket),
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_IOC,
    }
    res = mt5.order_send(req)
    print(json.dumps({'ticket': p.ticket, 'retcode': res.retcode, 'comment': res.comment, 'deal': res.deal, 'last_error': mt5.last_error()}, default=str))
print('remaining', json.dumps([p._asdict() for p in (mt5.positions_get() or [])], default=str))
