import requests, json, subprocess, time, os, re
from pathlib import Path

REPORT = []

def ok(s): REPORT.append(f'[OK]   {s}')
def fail(s, e=''): REPORT.append(f'[FAIL] {s} {e}')
def info(s): REPORT.append(f'[INFO] {s}')
def section(s): REPORT.append(f'\n===== {s} =====')

def run(cmd, timeout=10):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return -1, '', str(e)[:300]

def curl_raw(url, timeout=5):
    try:
        r = requests.get(url, timeout=timeout)
        ct = r.headers.get('content-type','')
        body = r.text[:220].replace('\n',' ')
        return r.status_code, ct, body
    except Exception as e:
        return None, '', str(e)[:220]

section('Docker services')
code, out, err = run('docker compose ps --format "{{.Name}}\t{{.State}}"')
if code == 0:
    info(out)
    ok('docker compose ps')
else:
    fail('docker compose ps', err[:200])

section('HTTP endpoints')
endpoints = {
    'hermes_rpc_7778_health': 'http://localhost:7778/health',
    'mt5_native_7779_account': 'http://localhost:7779/api/native/account',
    'mt5_native_7779_positions': 'http://localhost:7779/api/native/positions',
    'mt5_native_7779_bars': 'http://localhost:7779/api/native/latest_bars?instrument=XAUUSD&tf=M15&n=2',
    'mt5_native_7779_history_days': 'http://localhost:7779/api/native/history?days=2',
    'dashboard_8080_api_kanban': 'http://localhost:8080/api/kanban',
    'dashboard_8080_api_state': 'http://localhost:8080/api/kanban/state',
    'dashboard_8080_page_kanban': 'http://localhost:8080/kanban',
    'dashboard_8080_api_skills': 'http://localhost:8080/api/skills',
    'dashboard_8080_api_strategies': 'http://localhost:8080/api/strategies',
    'dashboard_8080_api_status': 'http://localhost:8080/api/status',
    'dashboard_8080_api_loops': 'http://localhost:8080/api/loops',
    'react_3000_api_kanban': 'http://localhost:3000/api/kanban',
    'react_3000_api_skills': 'http://localhost:3000/api/skills',
    'react_3000_api_loops': 'http://localhost:3000/api/loops',
    'react_3000_api_strategies': 'http://localhost:3000/api/strategies',
    'react_3000_api_status': 'http://localhost:3000/api/status',
    'react_3000_page_root': 'http://localhost:3000/',
    'backtester_5560': 'http://localhost:5560/health',
    'paper_trader_5561_stats': 'http://localhost:5561/stats',
    'paper_trader_5561_positions': 'http://localhost:5561/positions',
    'paper_trader_5561_history': 'http://localhost:5561/history?n=5',
    'execution_5563': 'http://localhost:5563/health',
    'deprecated_5558': 'http://localhost:5558/latest_bars?instrument=XAUUSD&tf=M15&n=2',
}
for name, url in endpoints.items():
    st, ct, body = curl_raw(url)
    if st == 200:
        ok(f'{name}: {url}')
        REPORT.append(f'    ct={ct} body={body}')
    elif st == 404:
        fail(f'{name}: {url}', '404')
    elif st == 500:
        fail(f'{name}: 500 server error')
    elif st is None:
        fail(f'{name}: unreachable')
    else:
        fail(f'{name}: HTTP {st}')

section('React frontend pages')
for p in ['/', '/kanban', '/logs', '/loops', '/strategies', '/trades', '/vault']:
    st, ct, body = curl_raw(f'http://localhost:3000{p}')
    if st == 200 and 'text/html' in ct:
        ok(f'react page {p}: 200 html')
    elif st == 200:
        fail(f'react page {p}: 200 but ct={ct}')
    else:
        fail(f'react page {p}: HTTP {st}')

section('Subagents')
code, out, err = run('powershell -NoProfile -ExecutionPolicy Bypass -Command \"Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName | ConvertTo-Json\"')
if code == 0 and out:
    try:
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        ids = [str(x.get('Id','')) for x in data if 'python' in str(x.get('ProcessName','')).lower()]
        ok(f'python processes: {len(ids)} PIDs: {",".join(ids[:30])}')
    except Exception:
        info(out[:300])
else:
    fail('Get-Process python', out[:200])
log_files = sorted(Path('.').glob('subagent_*.log'))
info(f'subagent log files: {len(log_files)}')
for lf in log_files[:10]:
    if lf.exists():
        lines = lf.read_text(encoding='utf-8', errors='ignore').splitlines()
        tail = lines[-6:] if lines else []
        info(f'{lf.name}: {tail[-3:]}')

section('Modified files checks')
checks = {
    'scripts/launch_subagents.py': ['mt5_subagent_contracts.json', 'subprocess.Popen', 'pid'],
    'dashboard/routes/kanban.py': ["/launch", "/stop", 'subprocess.Popen', 'psutil'],
    'dashboard/app.py': ["'/kanban'", 'render_template', 'kanban.html'],
    'dashboard/templates/kanban.html': ['Subagent Board', 'Launch All', 'Stop'],
    'src/App.tsx': ["'kanban'", 'Launch All', 'Stop', '/api/loops'],
    'scripts/start_all.ps1': ['launch_subagents.py', 'Subagent Board', '8080/kanban'],
    'hermes_rpc/autonomous_agent.py': ['http://localhost:7779', 'MT5_BRIDGE_URL', 'def get_bars'],
}
for path, needles in checks.items():
    p = Path(path)
    if not p.exists():
        fail(f'file missing: {path}')
        continue
    txt = p.read_text(encoding='utf-8', errors='ignore')
    missed = [n for n in needles if n not in txt]
    if missed:
        fail(f'{path}: missing {missed}')
    else:
        ok(f'{path}: expected strings present')

section('Deprecated reference scan')
deprecated = ['localhost:5558', 'localhost:5555', 'localhost:5556', 'localhost:5557']
hits = []
for p in Path('.').rglob('*.py'):
    try:
        txt = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    for d in deprecated:
        if d in txt:
            hits.append(f'{p}: {d}')
if hits:
    fail(f'deprecated references found: {hits[:20]}')
else:
    ok('no deprecated 5558/5555 references in .py files')

section('start_all.ps1 validation')
ps = Path('scripts/start_all.ps1')
if ps.exists():
    txt = ps.read_text(encoding='utf-8', errors='ignore')
    if 'launch_subagents.py' in txt and 'Subagent Board' in txt and '8080/kanban' in txt:
        ok('start_all.ps1 contains kanban board launch')
    else:
        fail('start_all.ps1 missing launch strings')
else:
    fail('start_all.ps1 missing')

section('Container file integrity')
container_checks = [
    ('dashboard', 'app.py', '/app/dashboard/app.py'),
    ('dashboard', 'routes/kanban.py', '/app/dashboard/routes/kanban.py'),
    ('dashboard', 'templates/kanban.html', '/app/dashboard/templates/kanban.html'),
]
for container, host_rel, container_path in container_checks:
    code2, out2, _ = run(f'docker exec {container} sh -c "test -f {container_path} && echo yes || echo no"')
    if code2 == 0 and 'yes' in out2:
        ok(f'container {container} has {container_path}')
    else:
        fail(f'container {container} missing {container_path}')

section('autonomous_agent.py defaults')
aap = Path('hermes_rpc/autonomous_agent.py')
if aap.exists():
    txt = aap.read_text(encoding='utf-8', errors='ignore')
    if 'http://localhost:7779' in txt and 'MT5_BRIDGE_URL' in txt:
        ok('autonomous_agent.py defaults point to 7779')
    else:
        fail('autonomous_agent.py wrong default URLs')

section('Compile checks')
code, out, err = run('python3 -m py_compile dashboard/app.py dashboard/routes/kanban.py hermes_rpc/autonomous_agent.py scripts/launch_subagents.py')
if code == 0:
    ok('py_compile passed')
else:
    fail('py_compile', err[:200])

section('Frontend build status')
if Path('dist/server.cjs').exists():
    ok('dist/server.cjs exists on host')
else:
    fail('dist/server.cjs missing on host')
if Path('dist/index.html').exists():
    ok('dist/index.html exists on host')
else:
    fail('dist/index.html missing on host')

print('\n'.join(REPORT))
Path('/tmp/system_check_report.txt').write_text('\n'.join(REPORT), encoding='utf-8')
info('report saved to /tmp/system_check_report.txt')
