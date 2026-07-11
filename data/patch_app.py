import os
print("[PATCH_APP] start")
path = "/app/dashboard/app.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
old = "    app.register_blueprint(rnd_bp, url_prefix='/api/rnd')\n"
new = "    app.register_blueprint(rnd_bp, url_prefix='/api/rnd')\n    app.register_blueprint(kanban_bp, url_prefix='/api/kanban')\n    app.register_blueprint(scheduler_bp, url_prefix='/api/scheduler')\n"
if old not in text:
    raise SystemExit("target registration block not found")
text = text.replace(old, new, 1)
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("[PATCH_APP] patched app.py")
