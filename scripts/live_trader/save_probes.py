import os, json, subprocess
from pathlib import Path

cases = [
    ("sell_limit_no_sl_tp", {"action":5,"symbol":"XAUUSD","volume":0.1,"price":4167.5,"type":3,"deviation":20,"magic":123456,"comment":"probe1","type_time":0,"type_filling":2}),
    ("sell_limit_no_sl_tp_int", {"action":5,"symbol":"XAUUSD","volume":0.1,"price":4167,"type":3,"deviation":20,"magic":123456,"comment":"probe1b","type_time":0,"type_filling":2}),
    ("buy_limit_no_sl_tp", {"action":5,"symbol":"XAUUSD","volume":0.1,"price":4157.0,"type":2,"deviation":20,"magic":123456,"comment":"probe2","type_time":0,"type_filling":2}),
    ("buy_limit_no_sl_tp_int", {"action":5,"symbol":"XAUUSD","volume":0.1,"price":4157,"type":2,"deviation":20,"magic":123456,"comment":"probe2b","type_time":0,"type_filling":2}),
    ("buy_stop_no_sl_tp", {"action":5,"symbol":"XAUUSD","volume":0.1,"price":4168.5,"type":4,"deviation":20,"magic":123456,"comment":"probe3","type_time":0,"type_filling":2}),
    ("sell_stop_no_sl_tp", {"action":5,"symbol":"XAUUSD","volume":0.1,"price":4140.5,"type":5,"deviation":20,"magic":123456,"comment":"probe4","type_time":0,"type_filling":2}),
    ("buy_limit_safe", {"action":5,"symbol":"XAUUSD","volume":0.1,"price":4143.55,"type":2,"deviation":20,"magic":123456,"comment":"probe5","type_time":0,"type_filling":2}),
    ("sell_limit_safe", {"action":5,"symbol":"XAUUSD","volume":0.1,"price":4168.45,"type":3,"deviation":20,"magic":123456,"comment":"probe6","type_time":0,"type_filling":2}),
]
outdir=r"C:\Users\user\Desktop\hermes_claude\scripts\live_trader"
for name,req in cases:
    path=Path(outdir)/f"probe_{name}.json"
    path.write_text(json.dumps(req), encoding='utf-8')
    pp=str(path)
    script=f"import sys,json; payload=json.load(open({repr(pp)},'r',encoding='utf-8')); print(json.dumps(payload))"
    print(name, 'saved')
