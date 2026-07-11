import os, sys
print("[PATCH] start")
APP = "/app"
for rel in ["dashboard/routes/trades.py", "dashboard/routes/kanban.py", "dashboard/routes/scheduler.py"]:
    host_path = "/c/Users/user/Desktop/hermes_claude/" + rel.replace("/", os.sep)
    container_path = os.path.join(APP, rel)
    with open(host_path, "rb") as src:
        data = src.read()
    with open(container_path, "wb") as dst:
        dst.write(data)
    print("[PATCH] wrote", container_path, len(data), "bytes")
print("[PATCH] complete")
