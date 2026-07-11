from pathlib import Path
import re

repo = Path("C:/Users/user/Desktop/hermes_claude")
files = [
    repo / "scripts" / "live_trader" / "xau_scalp_signals.py",
    repo / "scripts" / "live_trader" / "xau_live_session.py",
    repo / "scripts" / "live_trader" / "xau_position_watcher.py",
    repo / "scripts" / "live_trader" / "execution_operator.py",
]

new_path = r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075"

pattern = re.compile(r"mt5\.initialize\(\s*\)")
replacement = f"mt5.initialize(path=r\"{new_path}\")"

for f in files:
    text = f.read_text(encoding="utf-8")
    if pattern.search(text):
        text = pattern.sub(lambda m: replacement, text)
        f.write_text(text, encoding="utf-8")
        print(f"updated {f.name}")
    else:
        print(f"no change {f.name}")
