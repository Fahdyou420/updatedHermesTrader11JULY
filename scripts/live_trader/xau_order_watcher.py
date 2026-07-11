import argparse, json, os, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

WATCHER_LOG = Path.home() / "HermesLogs" / "xau_order_watcher.log"
WATCHER_LOG.parent.mkdir(parents=True, exist_ok=True)
PYTHON = r"C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe"
SCRIPT = Path(r"C:\Users\user\Desktop\hermes_claude\scripts\live_trader\xau_live_session.py")
TICK = 60


def run_once() -> str:
    env = {**os.environ, "XAU_CMD": "watch"}
    cmd = [PYTHON, str(SCRIPT)]
    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
        out = (res.stdout or "").strip().splitlines()
        text = out[-1] if out else (json.dumps({"status":"unknown"}, default=str))
    except Exception as e:
        text = json.dumps({"status":"error","msg":str(e)}, default=str)
    line = f"[{datetime.now(timezone.utc).isoformat()}] {text}"
    try:
        with WATCHER_LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    return line


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=12)
    args = parser.parse_args()
    n = 0
    while n < args.max:
        print(run_once())
        n += 1
        time.sleep(TICK)
