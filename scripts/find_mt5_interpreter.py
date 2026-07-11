#!/usr/bin/env python3
"""find_mt5_interpreter.py — prefer venv interpreters that can import FastAPI + MetaTrader5."""
import sys
from pathlib import Path
from importlib.util import find_spec

ROOT = Path(r"C:\Users\user\Desktop\hermes_claude")
CANDIDATES = [
    ROOT / "venv" / "Scripts" / "python.exe",
    ROOT / "hermes_rpc" / ".venv" / "Scripts" / "python.exe",
    ROOT / "hermes_rpc" / "venv" / "Scripts" / "python.exe",
    Path(r"C:\Python314\python.exe"),
    Path(r"C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe"),
    Path(r"C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"),
    Path(sys.executable),
]
seen = []
for c in CANDIDATES:
    if not c.exists() or c in seen:
        continue
    seen.append(c)
    ok = []
    for mod in ("fastapi", "uvicorn", "MetaTrader5", "pydantic_core"):
        ok.append((mod, bool(find_spec(mod))))
    print(c)
    for mod, found in ok:
        print(f"  {mod}: {'OK' if found else 'MISSING'}")
    if all(found for _, found in ok):
        print('  -> SELECTED')
        raise SystemExit(0)
    print()
print('none')
