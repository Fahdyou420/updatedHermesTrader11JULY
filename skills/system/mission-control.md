---
name: mission-control
description: "Single interface for starting, stopping, and checking every Hermes trading system department. Use when the user wants to pause/resume a department or the whole system, or inspect full system status."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, mission-control, operator, cron, kanban, department, pause, resume, status]
---

# Mission Control

Mission Control is the single interface for starting, stopping, and checking every department. Use this skill only for operator control and status inspection; it does not change strategy logic, trading decisions, or data pipelines.

## Hard Rules

- Always save pre-shutdown state before pausing anything. Resume only what was paused.
- Do not hide intentional blocked tasks; preserve their blocked state across shutdowns/resumes.
- Pausing a department pauses its cron jobs and Kanban task dispatch only.
- The Obsidian vault and ChromaDB are shared infrastructure. Only pause them during explicit full-system maintenance windows, never as part of normal department lifecycle.

## Exact Commands

### FULL SYSTEM STOP

```bash
# 1. Capture exact current state
python3 - <<'PY'
import json
from pathlib import Path

root = Path.home()/'.hermes'
cron = json.loads((root/'cron/jobs.json').read_text(encoding='utf-8'))
kb_path = root/'kanban/boards/hermes-trading-rd/kanban_tasks.json'
kb = json.loads(kb_path.read_text(encoding='utf-8'))

state = {
    'cron': [{'id': j['id'], 'name': j['name'], 'enabled': j.get('enabled', True), 'state': j.get('state'), 'tags': j.get('tags', [])} for j in cron.get('jobs', [])],
    'kanban': [{'id': t['id'], 'title': t.get('title'), 'status': t.get('status'), 'tags': t.get('tags', [])} for t in kb],
}
(root/'state/suspend_state.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
print('saved', root/'state/suspend_state.json')
PY

# 2. Pause every active cron job
python3 - <<'PY'
import json
from pathlib import Path
root=Path.home()/'.hermes'
for j in json.loads((root/'cron/jobs.json').read_text(encoding='utf-8')).get('jobs', []):
    print(j['id'], '|', j.get('name'), '|', j.get('tags'))
PY
# Then for each ID shown:
# hermes cron pause <id>

# 3. Block every non-blocked kanban task
python3 - <<'PY'
import json
from pathlib import Path
root=Path.home()/'.hermes'
kb=json.loads((root/'kanban/boards/hermes-trading-rd/kanban_tasks.json').read_text(encoding='utf-8'))
for t in kb:
    print(t['id'], '|', t.get('title'), '|', t.get('status'), '|', t.get('tags'))
PY
# Then for each task with status != blocked:
# hermes kanban block <id>
```

### FULL SYSTEM RESUME

```bash
# Resume only what was active before the last shutdown
python3 - <<'PY'
import json
from pathlib import Path
root=Path.home()/'.hermes'
ss=json.loads((root/'state/suspend_state.json').read_text(encoding='utf-8'))
for j in ss.get('cron', []):
    if j.get('enabled') and j.get('state') not in ('paused','disabled'):
        print('cron resume', j['id'], '|', j.get('name'))
for t in ss.get('kanban', []):
    if t.get('status') not in ('blocked','archived'):
        print('kanban unblock', t['id'], '|', t.get('title'))
PY
# Then run the printed statements exactly.
```

### SINGLE DEPARTMENT STOP/RESUME

```bash
# Stop one department only
python3 - <<'PY'
import json
from pathlib import Path
root=Path.home()/'.hermes'
ids={'cron':[],'kanban':[]}
for j in json.loads((root/'cron/jobs.json').read_text(encoding='utf-8')).get('jobs', []):
    if j.get('tags') and j['tags'][0]=='dept:execution':
        ids['cron'].append(j['id'])
kb=json.loads((root/'kanban/boards/hermes-trading-rd/kanban_tasks.json').read_text(encoding='utf-8'))
for t in kb:
    if t.get('tags') and t['tags'][0]=='dept:execution':
        ids['kanban'].append(t['id'])
print('cron ids', ids['cron'])
print('kanban ids', ids['kanban'])
PY
# Then:
# for id in <cron ids>: hermes cron pause <id>
# for id in <kanban ids>: hermes kanban block <id>

# Resume one department only
# for id in same saved cron ids: hermes cron resume <id>
# for id in same saved kanban ids: hermes kanban unblock <id>
```

### STATUS CHECK

```bash
hermes kanban list 2>&1
hermes cron list 2>&1
hermes curator status 2>&1
```

Quick health reads:

```bash
ls -l ~/AppData/Local/hermes/obsidian/MEMORY.md
python3 - <<'PY'
from pathlib import Path
print('MEMORY mtime:', Path('C:/Users/user/Desktop/hermes_claude/MEMORY.md').stat().st_mtime)
print('memory_sync mtime:', __import__('os.path').path.getmtime(__import__('pathlib').Path('C:/Users/user/AppData/Local/hermes/cron/jobs.json')))
PY
python3 - <<'PY'
# Fallback Chroma/health probe only if your deployed setup exposes its path here:
from pathlib import Path
print('cron json exists', (Path.home()/'.hermes/state/suspend_state.json').exists())
PY
```

## Department Tag Contract

Use these exact tags when creating or tagging cron jobs and kanban tasks:

- `dept:execution`
- `dept:backtester`
- `dept:knowledge-rnd`
- `dept:reliability`
- `dept:memory`
- `dept:curation`
- `dept:dashboard-sync`
- `dept:messaging`
- `dept:mt5-native`

## Memory/RAG Control Model

- Pausing a department pauses writes through that department’s workflow only.
- Shared Obsidian vault and ChromaDB remain live and readable by other running departments.
- Only do full-system maintenance pauses for the vault/ChromaDB specifically when requested as maintenance, not for normal department stop/resume.

## Provenance

- State snapshots are saved to `~/.hermes/state/suspend_state_<UTC>.json` before each shutdown cycle.
- Resume is a replay of that snapshot only; anything blocked before shutdown stays blocked afterward.
