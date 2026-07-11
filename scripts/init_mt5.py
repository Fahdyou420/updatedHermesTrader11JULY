"""Initialize MetaTrader5 and verify connection."""
import sys
from pathlib import Path

MT5_TERMINAL_PATH = r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075"

try:
    import MetaTrader5 as mt5
    print(f"[OK] MetaTrader5 package imported")
except Exception as e:
    print(f"[FAIL] Cannot import MetaTrader5: {e}")
    sys.exit(1)


def _try_init(path):
    ok = mt5.initialize(path=path)
    print(f"[INFO] initialize(path={path!r}) => {ok}, last_error={mt5.last_error()}")
    return ok


try:
    if not _try_init(MT5_TERMINAL_PATH):
        print("[INFO] Trying install-path fallback...")
        if not _try_init(r"C:\Program Files\MetaTrader 5\terminal64.exe"):
            print(f"[FAIL] mt5.initialize() failed")
            sys.exit(1)

    terminal_info = {
        "build": mt5.terminal_info().build,
        "name": mt5.terminal_info().name,
        "company": mt5.terminal_info().company,
        "connected": mt5.terminal_info().connected,
        "path": mt5.terminal_info().path,
    }
    print("[OK] MetaTrader5 initialized successfully")
    for k, v in terminal_info.items():
        print(f"   {k}: {v}")

    try:
        symbols = mt5.symbols_get("XAUUSD", "XAUUSD")
        if symbols:
            s = symbols[0]
            print(f"[OK] Symbol XAUUSD visible: {s.name}, digits={s.digits}, path={s.path}")
        else:
            print("[WARN] XAUUSD not visible in Market Watch (may need chart open)")
    except Exception as e:
        print(f"[WARN] symbols_get raised: {e}")

    try:
        vi = mt5.version()
        print(f"[INFO] MT5 API version: {vi}")
    except Exception as e:
        print(f"[WARN] version() raised: {e}")

finally:
    try:
        mt5.shutdown()
    except Exception as e:
        print(f"[WARN] shutdown raised: {e}")
    print("[INFO] MetaTrader5 shutdown cleanly")
