#!/usr/bin/env python3
"""Launch Hermes subagents from kanban contracts."""
import json, os, time, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTRACTS = REPO / "data/run/jobs/mt5_subagent_contracts.json"
STATE = REPO / "data/kanban/state.json"
PYTHON = Path(sys.executable)  # prefer venv; override with env SYSTEM_PYTHON
# Ensure a real working interpreter: prefer venv python, otherwise fall back to
# a cached working system python/python3 when the venv or default sys.executable
# would resolve to a broken Windows Store Python install.
_candidates = []
if 'SYSTEM_PYTHON' in os.environ:
    _candidates.append(Path(os.environ['SYSTEM_PYTHON']))
_venv = REPO / 'hermes_rpc/../venv/Scripts/python.exe'
if _venv.exists():
    _candidates.insert(0, _venv)
else:
    _candidates.extend([Path('python3'), Path('python')])
for _c in dict.fromkeys(_candidates):
    try:
        p = subprocess.run([str(_c), '--version'], check=True, capture_output=True, text=True)
        if p.returncode == 0 and _c.exists():
            PYTHON = _c
            break
    except Exception:
        continue
AGENT = REPO / "hermes_rpc/autonomous_agent.py"

def launch():
    contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    if isinstance(contracts, dict):
        contracts = contracts.get("tasks", [])
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"columns": {"in_progress": []}, "next_id": 1}
    # Reset stale in_progress cards so launch doesn't skip on dead PIDs.
    state["columns"]["in_progress"] = []
    state["next_id"] = 1
    existing = {t.get("task_id") for t in state.get("columns", {}).get("in_progress", [])}
    next_id = int(state.get("next_id", 1))
    for c in contracts:
        if not isinstance(c, dict):
            continue
        tid = c.get("task_id") or c.get("id")
        if tid in existing:
            continue
        log = REPO / f"subagent_{tid}.log"
        proc = subprocess.Popen(
            [str(PYTHON), str(AGENT), "--task", str(tid), "--task-num", str(c.get("order", 1))],
            cwd=str(REPO),
            stdout=log.open("a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            close_fds=True,
            creationflags=(getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0) | getattr(subprocess, 'DETACHED_PROCESS', 0)),
        )
        card = {
            "id": next_id,
            "text": f"[SUBBOARD] {c.get('title', tid)}",
            "dept": str(c.get("dept") or c.get("department") or "execution").strip().lower(),
            "status": "in_progress",
            "status_detail": "running",
            "tags": ["subagent", "launched", tid],
            "task_id": tid,
            "createdAt": time.time(),
            "pid": proc.pid,
        }
        state.setdefault("columns", {}).setdefault("in_progress", []).append(card)
        next_id += 1
        print(f"Launched {tid} pid={proc.pid}")
    state["next_id"] = next_id
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"Wrote state with {len(state['columns']['in_progress'])} tasks")

if __name__ == "__main__":
    launch()
