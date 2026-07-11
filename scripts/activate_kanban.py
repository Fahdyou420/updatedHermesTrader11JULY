#!/usr/bin/env python3
"""
Kanban Board Activator for Hermes Subagent System
Reads mt5_subagent_contracts.json, populates kanban, and starts execution.
"""
import json, time, sys, os, subprocess, threading
from pathlib import Path

BASE = Path("C:/Users/user/Desktop/hermes_claude")
KANBAN_STATE = BASE / "data/kanban/state.json"
CONTRACTS = BASE / "data/run/jobs/mt5_subagent_contracts.json"
OUTCOMES = BASE / "data/run/outcomes"
JOB_RUNNER = BASE / "data/run/mt5_job_runner.py"

def load_kanban():
    if not KANBAN_STATE.exists():
        return {"columns": {"todo": [], "in_progress": [], "review": [], "done": []}, "next_id": 1}
    return json.loads(KANBAN_STATE.read_text(encoding="utf-8"))

def save_kanban(state):
    KANBAN_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def activate_board():
    """Load contracts and populate kanban todo column."""
    state = load_kanban()
    
    # Clear existing tasks to avoid duplicates
    for col in state["columns"].values():
        col.clear()
    
    contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    next_id = 1
    
    task_map = {
        "mt5_subagent_backtest_01": "BACKTESTER",
        "mt5_subagent_pattern_01": "BACKTESTER", 
        "mt5_subagent_killzone_01": "RESEARCH"
    }
    
    for job in contracts:
        task = {
            "id": next_id,
            "text": f"[{task_map.get(job['task_id'], 'GENERAL')}] {job['title']}",
            "dept": task_map.get(job['task_id'], "general").lower(),
            "status": "todo",
            "tags": ["subagent", "mt5", job['task_id']],
            "task_id": job['task_id'],
            "createdAt": time.time(),
            "objective": job.get("objective", ""),
            "deliverables": job.get("deliverables", []),
            "constraints": job.get("constraints", []),
            "status_detail": "pending"
        }
        state["columns"]["todo"].append(task)
        next_id += 1
    
    state["next_id"] = next_id
    save_kanban(state)
    print(f"✓ Kanban activated: {len(contracts)} tasks loaded into todo column")
    return state

def run_job_runner():
    """Execute the MT5 job runner to generate manifests."""
    print("→ Running MT5 job runner...")
    result = subprocess.run(
        [sys.executable, str(JOB_RUNNER)],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode == 0:
        print("✓ Job runner completed")
        print(result.stdout[:500])
    else:
        print(f"✗ Job runner failed: {result.stderr[:200]}")
    return result.returncode == 0

def verify_outcomes():
    """Check that outcome manifests exist."""
    manifests = list(OUTCOMES.glob("*_manifest.json"))
    print(f"→ Found {len(manifests)} outcome manifests")
    for m in manifests[:5]:
        data = json.loads(m.read_text(encoding="utf-8"))
        print(f"  {m.name}: status={data.get('status')}")
    return len(manifests) > 0

def main():
    print("=" * 60)
    print("  KANBAN BOARD ACTIVATOR")
    print("=" * 60)
    
    # Step 1: Activate kanban board
    state = activate_board()
    print(f"\nKanban state: {json.dumps(state['columns'], indent=2)}")
    
    # Step 2: Run job runner
    run_job_runner()
    
    # Step 3: Verify outcomes
    verify_outcomes()
    
    # Step 4: Reload kanban to show updated state
    state = load_kanban()
    print(f"\n✓ Final kanban state:")
    print(f"  todo: {len(state['columns']['todo'])}")
    print(f"  in_progress: {len(state['columns']['in_progress'])}")
    print(f"  review: {len(state['columns']['review'])}")
    print(f"  done: {len(state['columns']['done'])}")
    
    print("\n" + "=" * 60)
    print("  KANBAN BOARD FULLY ACTIVATED")
    print("=" * 60)

if __name__ == "__main__":
    main()
