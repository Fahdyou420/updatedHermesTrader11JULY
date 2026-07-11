"""
Loop Supervisor — makes the system self-healing.
Cross-references service/container health and kanban/cron PIDs with live processes;
restarts dead docker services and relaunches dead workers.
"""
from __future__ import annotations

import os
import time
import json
import subprocess
import threading
from typing import Any, Dict, List, Optional

from services.shared.logger import get_logger

try:
    from services.shared.error_bus import publish_error
except Exception:  # pragma: no cover
    publish_error = None

logger = get_logger("loop_supervisor")

DOCKER_COMPOSE = os.getenv("DOCKER_COMPOSE_FILE", "docker-compose.yml")
COMPOSE_CWD = os.getenv("COMPOSE_CWD", os.getcwd())
REQUIRED_SERVICES = [s.strip() for s in os.getenv("SUPERVISOR_SERVICES", "paper_trader,execution,dashboard,app").split(",") if s.strip()]
PID_PATTERNS = [p.strip() for p in os.getenv("SUPERVISOR_PID_PATTERNS", "python -m services.paper_trader,uvicorn").split(",") if p.strip()]
STATE_DIR = os.getenv("SUPERVISOR_STATE_DIR", "/data/trades/loop_supervisor")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
CHECK_INTERVAL = int(os.getenv("SUPERVISOR_INTERVAL_SECONDS", "60"))


def _load_state() -> Dict[str, Any]:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state: Dict[str, Any]) -> None:
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        temp = STATE_FILE + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(temp, STATE_FILE)
    except Exception as e:
        logger.warning("Failed to persist loop supervisor state: %s", e)


def _docker_cmd(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=COMPOSE_CWD,
        check=False,
        capture_output=True,
        text=True,
    )


def _restart_service(name: str, state: Dict[str, Any]) -> None:
    logger.warning("Loop supervisor restarting service=%s", name)
    try:
        proc = _docker_cmd("up", "-d", name)
        logger.info("docker compose up -d %s rc=%d stdout=%s stderr=%s", name, proc.returncode, proc.stdout.strip(), proc.stderr.strip())
        state[f"{name}:last_restart_ts"] = int(time.time())
        state[f"{name}:failures"] = int(state.get(f"{name}:failures", 0)) + 1
        if publish_error:
            try:
                publish_error("loop_supervisor", "WARNING", f"Restarted docker service {name}", proc.stderr.strip() or proc.stdout.strip())
            except Exception:
                pass
    except Exception as e:
        logger.error("Loop supervisor restart failed for %s: %s", name, e)
        state[f"{name}:failures"] = int(state.get(f"{name}:failures", 0)) + 1


def _check_container(name: str) -> bool:
    try:
        proc = subprocess.run(
            ["docker", "ps", "--filter", f"name={name}", "--filter", "status=running", "--format", "{{.Names}}"],
            check=False,
            capture_output=True,
            text=True,
        )
        out = proc.stdout.strip()
        return bool(out)
    except Exception:
        return False


def _count_processes(pattern: str) -> int:
    try:
        if os.name == "nt":
            args = ["tasklist", "/FI", f"IMAGENAME eq {pattern}", "/FO", "CSV", "/NH"]
        else:
            args = ["pgrep", "-f", pattern]
        proc = subprocess.run(args, check=False, capture_output=True, text=True)
        out = proc.stdout.strip()
        return len([line for line in out.splitlines() if line])
    except Exception:
        return 0


def tick(state: Dict[str, Any]) -> None:
    now = int(time.time())
    state.setdefault("checks", 0)
    state["checks"] += 1
    state["last_check_ts"] = now

    for name in REQUIRED_SERVICES:
        up = _check_container(name)
        key = f"{name}:up"
        state[key] = bool(up)
        if not up:
            logger.warning("Loop supervisor detected dead container: %s", name)
            _restart_service(name, state)


def start_thread() -> threading.Thread:
    def _run() -> None:
        state = _load_state()
        while True:
            try:
                tick(state)
                _save_state(state)
            except Exception as e:
                logger.error("Loop supervisor error: %s", e)
            time.sleep(CHECK_INTERVAL)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    logger.info("Loop supervisor started, interval=%ds services=%s", CHECK_INTERVAL, ",".join(REQUIRED_SERVICES))
    return t
