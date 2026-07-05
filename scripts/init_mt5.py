"""Initialize MetaTrader5 and verify connection."""
import sys
import time

try:
    import MetaTrader5 as mt5
    print(f"[OK] MetaTrader5 package imported (version info unavailable via public API)")
except Exception as e:
    print(f"[FAIL] Cannot import MetaTrader5: {e}")
    sys.exit(1)

try:
    # Try initialize without path first; if fails, try explicit path
    if not mt5.initialize():
        print(f"[INFO] Default init failed; trying explicit path...")
        if not mt5.initialize(path=r"C:\Program Files\MetaTrader 5\terminal64.exe"):
            print(f"[FAIL] mt5.initialize() failed, error code = {mt5.last_error()}")
            mt5.shutdown()
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

    # Verify we can fetch basic data
    symbols = mt5.symbols_get("XAUUSD", "XAUUSD")
    if symbols:
        s = symbols[0]
        print(f"[OK] Symbol XAUUSD visible: {s.name}, digits={s.digits}, path={s.path}")
    else:
        print("[WARN] XAUUSD not visible in Market Watch (may need chart open)")

    # get version info if available
    vi = mt5.version()
    print(f"[INFO] MT5 API version: {vi}")

finally:
    mt5.shutdown()
    print("[INFO] MetaTrader5 shutdown cleanly")
