import os, sys
from pathlib import Path

MT5_TERMINAL_PATH = os.getenv(
    "MT5_TERMINAL_PATH",
    r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075",
)

try:
    import MetaTrader5 as mt5
except ImportError:
    print("MetaTrader5 package missing; python -m pip install MetaTrader5")
    sys.exit(2)

if not Path(MT5_TERMINAL_PATH).is_dir():
    print(f"MT5 terminal path not found: {MT5_TERMINAL_PATH}")
    sys.exit(3)

ok = mt5.initialize(path=MT5_TERMINAL_PATH)
if not ok:
    print(f"MT5 initialize() failed={mt5.last_error()} path={MT5_TERMINAL_PATH}")
    sys.exit(4)

print(f"MT5 initialized path={MT5_TERMINAL_PATH}")
acc = mt5.account_info()
if acc is None:
    print(f"account_info failed={mt5.last_error()}")
    sys.exit(5)
print({"login": acc.login, "server": acc.server, "balance": acc.balance, "equity": acc.equity, "leverage": acc.leverage})
mt5.shutdown()
