import MetaTrader5 as mt5
import json
mt5.initialize(path=r"C:\Program Files\MetaTrader 5	erminal64.exe")
for pos in mt5.positions_get() or []:
    typ = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(pos.symbol)
    price = tick.bid if pos.type == 0 else tick.ask
    req = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': pos.symbol,
        'volume': pos.volume,
        'type': typ,
        'position': pos.ticket,
        'price': price,
        'deviation': 20,
        'magic': 123456,
        'comment': 'close_' + str(pos.ticket),
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_IOC,
    }
    res = mt5.order_send(req)
    print(json.dumps({'ticket': pos.ticket, 'retcode': res.retcode, 'comment': res.comment, 'deal': res.deal, 'last_error': mt5.last_error()}, default=str))
print('remaining', len(mt5.positions_get() or []))
