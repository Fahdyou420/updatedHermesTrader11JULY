import os, json, subprocess, time
from flask import Blueprint, request, jsonify

kanban_bp = Blueprint('kanban', __name__)

BASE = os.getenv("KANBAN_DATA_DIR", "/data/kanban")
STATE_FILE = os.path.join(BASE, "state.json")
JOBS_FILE = os.getenv("KANBAN_JOBS", "/data/run/jobs/mt5_subagent_contracts.json")
os.makedirs(BASE, exist_ok=True)

REPO = os.getenv("HERMES_REPO", "/app")
AGENT_SCRIPT = os.path.join(REPO, "hermes_rpc", "autonomous_agent.py")
PYTHON = os.getenv("SYSTEM_PYTHON", "python")

def read_state():
    if not os.path.exists(STATE_FILE):
        write_state({"columns": {"todo": [], "in_progress": [], "review": [], "done": []}, "next_id": 1})
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

@kanban_bp.route('/state', methods=['GET'])
def get_state():
    return jsonify(read_state())

@kanban_bp.route('/task', methods=['POST'])
def create_task():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or data.get("title") or data.get("task") or "").strip()
    dept = str(data.get("dept") or data.get("department") or "general").strip().lower()
    if not text:
        return jsonify({"error": "text/title required"}), 400
    state = read_state()
    task = {"id": state["next_id"], "text": text, "dept": dept, "status": "todo", "tags": [], "createdAt": time.time()}
    state["columns"]["todo"].append(task)
    state["next_id"] = int(state["next_id"]) + 1
    write_state(state)
    return jsonify(task), 201

@kanban_bp.route('/task/move', methods=['POST'])
def move_task():
    data = request.get_json(silent=True) or {}
    task_id = int(data.get("id") or 0)
    to = str(data.get("to") or "").strip().lower()
    if not task_id or to not in {"todo", "in_progress", "review", "done"}:
        return jsonify({"error": "id and to column required"}), 400
    state = read_state()
    item = None
    for items in state["columns"].values():
        for idx, cand in enumerate(items):
            if cand.get("id") == task_id:
                item = cand
                del items[idx]
                break
        if item:
            break
    if not item:
        return jsonify({"error": "task not found"}), 404
    item["status"] = to
    state["columns"][to].append(item)
    write_state(state)
    return jsonify(item)

@kanban_bp.route('/moves', methods=['POST'])
def enqueue_move_background():
    data = request.get_json(silent=True) or {}
    payload = json.dumps({"event": "kanban_move", "data": data})
    try:
        import redis as redis_lib
        r = redis_lib.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True)
        r.publish("KANBAN_EVENT", payload)
    except Exception as e:
        return jsonify({"error": str(e), "queued": payload}), 500
    return jsonify({"queued": True, "payload": payload})

@kanban_bp.route('/launch', methods=['POST'])
def launch_subboard():
    """Read subagent contracts and spawn them as background processes."""
    data = request.get_json(silent=True) or {}
    mode = (data.get("mode") or "all").strip().lower()
    if not os.path.exists(JOBS_FILE):
        return jsonify({"error": f"jobs file not found: {JOBS_FILE}"}), 404
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            payload = json.load(f)
        tasks = payload.get("tasks", []) if isinstance(payload, dict) else payload
    except Exception as e:
        return jsonify({"error": f"invalid jobs file: {e}"}), 400

    state = read_state()
    existing = {t.get("task_id") for t in state.get("columns", {}).get("in_progress", []) if t.get("pid")}
    next_id = int(state.get("next_id", 1))
    launched = []
    for t in tasks:
        tid = str(t.get("id") or t.get("task_id") or "").strip()
        if mode != "all" and mode != tid:
            continue
        if tid in existing:
            launched.append({"task_id": tid, "status": "already_running"})
            continue
        log_path = os.path.join(BASE, f"subagent_{tid}.log")
        cmd = [PYTHON, AGENT_SCRIPT, "--task", tid, "--task-num", str(t.get("order", 1))]
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=REPO,
                stdout=open(log_path, "a", encoding="utf-8"),
                stderr=subprocess.STDOUT,
                close_fds=True,
            )
        except Exception as e:
            return jsonify({"error": f"failed to launch {tid}: {e}"}), 500

        card = {
            "id": next_id,
            "text": f"[SUBBOARD] {t.get('title') or tid}",
            "dept": str(t.get("dept") or "execution").strip().lower(),
            "status": "in_progress",
            "status_detail": "running",
            "tags": ["subagent", "launched", tid],
            "task_id": tid,
            "createdAt": time.time(),
            "pid": proc.pid,
            "cmd": " ".join(cmd),
            "log": log_path,
        }
        state.setdefault("columns", {}).setdefault("in_progress", []).append(card)
        next_id += 1
        launched.append({"task_id": tid, "pid": proc.pid, "log": log_path})
    state["next_id"] = next_id
    write_state(state)
    return jsonify({"launched": launched, "total_in_progress": len(state["columns"]["in_progress"])}), 202

@kanban_bp.route('/stop', methods=['POST'])
def stop_task():
    data = request.get_json(silent=True) or {}
    try:
        task_id = int(data.get("id") or 0)
    except Exception:
        return jsonify({"error": "id must be int"}), 400
    state = read_state()
    item = None
    for col in state.get("columns", {}).values():
        for cand in col:
            if cand.get("id") == task_id:
                item = cand
                break
        if item:
            break
    if not item:
        return jsonify({"error": "task not found"}), 404
    pid = item.get("pid")
    if pid:
        try:
            os.kill(pid, 9)
            item["status_detail"] = "stopped"
            item["pid"] = None
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    item["status"] = "done"
    state.setdefault("columns", {}).setdefault("done", []).append(item)
    write_state(state)
    return jsonify(item)

@kanban_bp.route('/', methods=['GET'])
@kanban_bp.route('', methods=['GET'])
def kanban_index():
    return jsonify({"columns": read_state()["columns"], "next_id": read_state()["next_id"]})
