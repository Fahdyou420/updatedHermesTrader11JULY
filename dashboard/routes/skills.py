import os, json, glob
from flask import Blueprint, request, jsonify

skills_bp = Blueprint('skills', __name__)

HERMES_SKILLS_DIR = os.getenv("HERMES_SKILLS_DIR", os.path.expanduser("~/AppData/Local/hermes/skills"))
LOCAL_SKILLS_DIR = os.getenv("HERMES_SKILLS_DIR", HERMES_SKILLS_DIR)
DOCKER_SKILLS_DIR = "/data/skills"
SEARCH_DIRS = [LOCAL_SKILLS_DIR, DOCKER_SKILLS_DIR]


def _read_skill_meta(path: str):
    out = {"name": os.path.basename(path), "path": path, "description": "", "successRate": 0, "usageCount": 0, "updatedAt": ""}
    try:
        if path.endswith(".md"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read(4000)
            if text.startswith("---"):
                end = text.find("---", 3)
                if end != -1:
                    fm = text[3:end]
                    for line in fm.splitlines():
                        line = line.strip()
                        if line.startswith("name:"):
                            out["name"] = line.split(":", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("description:"):
                            out["description"] = line.split(":", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("successRatePercent:") or line.startswith("successRate:"):
                            try:
                                out["successRate"] = float(line.split(":", 1)[1].strip())
                            except Exception:
                                pass
                        elif line.startswith("usageCount:") or line.startswith("usage:"):
                            try:
                                out["usageCount"] = int(line.split(":", 1)[1].strip())
                            except Exception:
                                pass
                        elif line.startswith("updatedAt:") or line.startswith("date:"):
                            out["updatedAt"] = line.split(":", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return out


@skills_bp.route('/', methods=['GET'])
@skills_bp.route('', methods=['GET'])
def list_skills():
    query = (request.args.get('q') or '').lower()
    items = []
    seen = set()
    for base in SEARCH_DIRS:
        if not os.path.isdir(base):
            continue
        for path in glob.glob(os.path.join(base, "**", "SKILL.md"), recursive=True):
            items.append(path)
        for path in glob.glob(os.path.join(base, "**", "*.md"), recursive=True):
            if os.path.basename(path) not in {"README.md", "CHANGELOG.md"}:
                items.append(path)
    uniq = []
    for path in items:
        if path not in seen:
            seen.add(path)
            uniq.append(path)
    out = []
    for path in uniq:
        meta = _read_skill_meta(path)
        if query and query not in (meta.get("name","") + " " + meta.get("description","")).lower():
            continue
        out.append({
            "name": meta.get("name") or os.path.basename(path),
            "description": meta.get("description") or "",
            "successRate": meta.get("successRate") or 0,
            "usageCount": meta.get("usageCount") or 0,
            "updatedAt": meta.get("updatedAt") or "",
            "path": path,
        })
    out.sort(key=lambda x: x.get("name","").lower())
    return jsonify(out)


@skills_bp.route('/add', methods=['POST'])
def add_skill():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name') or payload.get('path') or '').strip()
    description = str(payload.get('description') or '').strip()
    code = str(payload.get('code') or payload.get('content') or '').strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    target = None
    for base in SEARCH_DIRS:
        try:
            os.makedirs(base, exist_ok=True)
            candidate = os.path.join(base, name if name.endswith('.md') else name + '.md')
            target = candidate
            with open(candidate, 'w', encoding='utf-8') as f:
                f.write(code or description or name)
            break
        except Exception:
            target = None
    if not target:
        return jsonify({"error": "unable to write skill file"}), 500
    return jsonify({"ok": True, "path": target})
