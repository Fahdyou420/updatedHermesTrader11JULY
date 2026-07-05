# MT5 Terminal + History Integration Fix

## Verified state on this machine
- `terminal64.exe` is reachable at `C:\Program Files\MetaTrader 5\terminal64.exe`.
- `MetaTrader5` Python package initializes successfully.
- `mt5.terminal_info().connected == True`.
- Terminal build `5833`, account `1513815135`, FTMO-Demo, leverage `1:100`.

## History API note
- `mt5.history_deals_get()` from this account returns `0` results across every range tested.
- Use Hermes bridge `/live_history` as the reliable source for closed XAUUSD trades.
- For reading current open positions, history on this accounts, or SaaS fallback, prefer bridge or broker export files.

## How to use
1. `python scripts/init_mt5.py`
2. If history API is empty, use Hermes bridge `http://localhost:5558/live_history`.
3. Continue downstream analysis via `scripts/xau_live_history_review.py`.
