import json, os, glob, time, requests, redis
from flask import Blueprint, request, jsonify

scheduler_bp = Blueprint("scheduler", __name__)
DATA = os.getenv("SCHEDULER_DATA_DIR", "/data/scheduler")
os.makedirs(DATA, exist_ok=True)

def _read(name, default):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write(name, obj):
    p = os.path.join(DATA, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

@scheduler_bp.route("/jobs", methods=["GET"])
def jobs_list():
    jobs = _read("jobs.json", [])
    events = _read("events.json", [])[-500:]
    return jsonify({"jobs": jobs, "events": events})

@scheduler_bp.route("/skills", methods=["GET"])
def skills_list():
    patterns = [
        "C:/Users/user/AppData/Local/hermes/skills/**/SKILL.md",
        "C:/Users/user/Desktop/hermes_claude/skills/**/SKILL.md",
    ]
    items = []
    for pat in patterns:
        for path in glob.glob(pat, recursive=True):
            try:
                txt = open(path, "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            name = os.path.basename(os.path.dirname(path))
            items.append({"name": name, "path": path, "preview": txt[:180].replace("\n", " ")})
    items.sort(key=lambda x: x["name"].lower())
    return jsonify(items)

@scheduler_bp.route("/queue", methods=["GET"])
def queue_view():
    q = _read("queue.json", [])
    return jsonify({"queue": q, "len": len(q), "updated": int(time.time())})

@scheduler_bp.route("/queue/add", methods=["POST"])
def queue_add():
    data = request.get_json(silent=True) or {}
    item = {
        "id": str(int(time.time()*1000)), "text": data.get("text"), "dept": data.get("dept", "general"),
        "status": "queued", "createdAt": int(time.time())
    }
    q = _read("queue.json", [])
    q.append(item)
    _write("queue.json", q)
    try:
        redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True).publish("SCHEDULER_EVENT", json.dumps({"event": "queue_add", "data": item}))
    except Exception:
        pass
    return jsonify(item), 201

@scheduler_bp.route('/', methods=['GET'])
@scheduler_bp.route('', methods=['GET'])
def scheduler_index():
    jobs = _read("jobs.json", [])
    queue = _read("queue.json", [])
    events = _read("events.json", [])[-500:]
    return jsonify({"jobs": jobs, "queue": queue, "events": events})
