"""OmniCore MT5 job runner.
Reads `data/run/jobs/mt5_subagent_contracts.json` and writes outputs under `data/run/outcomes/`.
This is a monitor-only executor: it creates contract manifests for MT5 testing.
"""
import json
from pathlib import Path

BASE = Path("C:/Users/user/Desktop/hermes_claude")
IN_PATH = BASE / "data/run/jobs/mt5_subagent_contracts.json"
OUT_DIR = BASE / "data/run/outcomes"
OUT_DIR.mkdir(parents=True, exist_ok=True)

jobs = json.loads(IN_PATH.read_text(encoding="utf-8"))
manifest = {
  "orchestrator": "omnicore_mt5_job_runner",
  "mode": "paper_test",
  "jobs": []
}

for job in jobs:
    out_path = OUT_DIR / f"{job['task_id']}_manifest.json"
    payload = {
        "task_id": job["task_id"],
        "status": "ready",
        "entry_path": str(IN_PATH),
        "deliverables": job.get("deliverables", []),
        "constraints": job.get("constraints", []),
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    manifest["jobs"].append(payload)
    print(job["task_id"], "=>", out_path)

print(json.dumps(manifest, indent=2))
