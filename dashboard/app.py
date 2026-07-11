import os
import sys
import json
import requests
import redis as redis_lib
from flask import Flask, Response, redirect, jsonify, render_template, request
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv(override=True)  # override=True ensures .env wins over stale system/user env vars

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from routes.chat import chat_bp
from routes.vault import vault_bp
from routes.strategy import strategy_bp
from routes.trades import trades_bp
from routes.rnd import rnd_bp
from routes.kanban import kanban_bp
from routes.scheduler import scheduler_bp
from routes.skills import skills_bp

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(vault_bp, url_prefix='/api/vault')
app.register_blueprint(strategy_bp, url_prefix='/api/strategy')
app.register_blueprint(trades_bp, url_prefix='/api/trades')
app.register_blueprint(rnd_bp, url_prefix='/api/rnd')
app.register_blueprint(kanban_bp, url_prefix='/api/kanban')
app.register_blueprint(scheduler_bp, url_prefix='/api/scheduler')
app.register_blueprint(skills_bp, url_prefix='/api/skills')

@app.route('/api/strategies', methods=['GET'])
def api_strategies_from_pack():
    pack_path = os.path.join('/app/data/rnd', 'xau_native_strategy_pack.json')
    try:
        if os.path.exists(pack_path):
            with open(pack_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            cards = raw
            if isinstance(raw, dict):
                cards = raw.get('strategies') or raw.get('cards') or raw.get('items') or [raw]
            if not isinstance(cards, list):
                cards = [cards]
            return jsonify({'items': [dict(card or {}, source='local', status=(card or {}).get('status', 'ready')) for card in cards]})
    except Exception:
        pass
    return jsonify({'items': []})


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
MT5_BRIDGE_URL = os.getenv("MT5_BRIDGE_URL", "http://mt5_bridge:5558")
NATIVE_MT5_URL = os.getenv("NATIVE_MT5_URL", "http://host.docker.internal:7779")
PREPROCESSOR_URL = os.getenv("PREPROCESSOR_URL", "http://preprocessor:5559")
PAPER_TRADER_URL = os.getenv("PAPER_TRADER_URL", "http://paper_trader:5561")
HERMES_RPC_URL = os.getenv("HERMES_RPC_URL", "http://host.docker.internal:7778")
EXECUTION_URL = os.getenv("EXECUTION_URL", "http://execution:5563")
CHROMADB_URL = os.getenv("CHROMADB_URL", "http://chromadb:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
NOUS_URL = os.getenv("NOUS_URL", "https://inference-api.nousresearch.com/v1")
NOUS_API_KEY = os.getenv("NOUS_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MT5_TESTNET_URL = os.getenv("MT5_TESTNET_URL", "")
TRADES_DATA_DIR = os.getenv("TRADES_DATA_DIR", "/data/trades")
OBSIDIAN_VAULT_ROOT = os.getenv("OBSIDIAN_VAULT_ROOT", "/data/obsidian")
os.makedirs(TRADES_DATA_DIR, exist_ok=True)
if not os.path.exists(OBSIDIAN_VAULT_ROOT):
    os.makedirs(OBSIDIAN_VAULT_ROOT, exist_ok=True)


def _get(url: str, timeout: int = 5):
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "hermes-dashboard"}), 200


@app.route('/api/status', methods=['GET'])
def system_status():
    """Real service health checks for all components."""
    def check(url, timeout=2):
        try:
            r = requests.get(url, timeout=timeout)
            return r.status_code == 200
        except Exception:
            return False

    llm_tier = "offline"
    llm_note = "nous/gemini unreachable"
    try:
        nous_ok = bool(NOUS_API_KEY) and check(f"{NOUS_URL}/models", timeout=3)
    except Exception:
        nous_ok = False
    try:
        gemini_ok = check("https://generativelanguage.googleapis.com/v1beta/models", timeout=3)
    except Exception:
        gemini_ok = False
    if nous_ok and gemini_ok:
        llm_tier = "nous+gemi"
        llm_note = "Nous Portal primary, Gemini active"
    elif nous_ok:
        llm_tier = "nous"
        llm_note = "Nous Portal active"
    elif gemini_ok:
        llm_tier = "gemini"
        llm_note = "Gemini fallback only"
    else:
        llm_tier = "offline"
        llm_note = "nous/gemini unreachable"

    rpc_ok = check(f"{HERMES_RPC_URL}/health", timeout=5)
    
    mt5_ok = False
    native_mt5_ok = False
    try:
        r = requests.get(f"{NATIVE_MT5_URL}/health", timeout=2)
        if r.status_code == 200:
            native_mt5_ok = bool(r.json().get("native_mt5", False))
            mt5_ok = native_mt5_ok
    except Exception:
        pass

    redis_ok = False
    try:
        r = redis_lib.Redis.from_url(REDIS_URL, socket_connect_timeout=2)
        r.ping()
        redis_ok = True
        r.close()
    except Exception:
        pass

    chroma_ok = check(f"{CHROMADB_URL}/api/v1/heartbeat") or check(f"{CHROMADB_URL}/api/v2/auth")
    obsidian_ok = os.path.exists("/data/obsidian")

    status = lambda ok: "connected" if ok else "disconnected"
    mt5_status = status(mt5_ok)

    return jsonify({
        "llm_cascade": {
            "active": llm_tier,
            "note": llm_note,
            "ollama": "intentionally_offline",
        },
        "hermesRpc": status(rpc_ok),
        "mt5Zmq": {"data": mt5_status, "draw": mt5_status, "order": mt5_status},
        "mt5Native": status(native_mt5_ok),
        "redis": status(redis_ok),
        "chromaDb": status(chroma_ok),
        "obsidian": status(obsidian_ok)
    })


@app.route('/api/market/price', methods=['GET'])
def get_market_price():
    """Live price from native MT5 first, then token preprocessor/MT5 bridge."""
    data = _get(f"{NATIVE_MT5_URL}/api/native/latest_bars?instrument=XAUUSD&tf=M15&n=1", timeout=4)
    if data and isinstance(data, list) and len(data) > 0 and data[-1].get('close'):
        return jsonify({"price": float(data[-1].get("close", 0.0))})
    if MT5_TESTNET_URL:
        data = _get(f"{MT5_TESTNET_URL}/latest_bars?instrument=XAUUSD&tf=M15&n=1", timeout=5)
        if data and isinstance(data, list) and len(data) > 0:
            return jsonify({"price": float(data[-1].get("close", 0.0))})
    data = _get(f"{MT5_BRIDGE_URL}/latest_bars?instrument=XAUUSD&tf=M15&n=1", timeout=5)
    if data and isinstance(data, list) and len(data) > 0:
        return jsonify({"price": float(data[-1].get("close", 0.0))})
    return jsonify({"price": 0.0})


@app.route('/api/errors', methods=['GET'])
def get_errors():
    """Return recent errors from the centralized Redis error bus."""
    try:
        from services.shared.error_bus import get_recent_errors
        n = int(request.args.get('n', 100))
        return jsonify(get_recent_errors(n))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/market', methods=['GET'])
@app.route('/api/market/price', methods=['POST', 'GET'])
def api_market_unpinned():
    return get_market_price()


@app.route('/api/llm/status', methods=['GET'])
def llm_status():
    try:
        r = redis_lib.Redis.from_url(REDIS_URL, decode_responses=True)
        data = r.get("LLM_ACTIVE_STATUS")
        if data:
            return jsonify(json.loads(data))
    except Exception:
        pass
    return jsonify({"tier": "none", "model": "none"})


@app.route('/api/logs/stream', methods=['GET'])
def stream_system_logs():
    def event_generator():
        pubsub = None
        try:
            r = redis_lib.Redis.from_url(REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            pubsub.subscribe("SYSTEM_LOGS")
            yield f"data: {json.dumps({'event': 'connected', 'message': 'SSE Log stream established'})}\n\n"
            for message in pubsub.listen():
                if message and message['type'] == 'message':
                    yield f"data: {message['data']}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
        finally:
            if pubsub:
                try: pubsub.unsubscribe()
                except: pass
    return Response(event_generator(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no'
    })


@app.route('/terminal')
def view_terminal():
    return render_template('terminal.html', active_page='terminal')


@app.route('/knowledge')
def view_knowledge():
    return render_template('knowledge.html', active_page='knowledge')


@app.route('/strategy')
def view_strategy():
    return render_template('strategy.html', active_page='strategy')


@app.route('/trades')
def view_trades():
    return render_template('trades.html', active_page='trades')


@app.route('/rnd')
def view_rnd():
    return render_template('rnd.html', active_page='rnd')


@app.route('/logs')
def view_logs():
    return render_template('logs.html', active_page='logs')


@app.route('/kanban')
def view_kanban():
    return render_template('kanban.html', active_page='kanban')


@app.route('/scheduler')
def view_scheduler():
    return render_template('scheduler.html', active_page='scheduler')


@app.route('/')
def home_redirect():
    return redirect('/terminal')


@app.route('/api/trades', methods=['GET'])
def api_trades_index():
    n = request.args.get('n', 399)
    source = (request.args.get('source') or '').lower().strip()
    jobs = [
        '/api/trades/positions?n=' + str(n),
        '/api/trades/history?n=' + str(n),
        '/api/trades/live_history?n=' + str(n) + '&instrument=' + request.args.get('instrument','XAUUSD'),
        '/api/trades/native_positions',
        '/api/trades/native_history?days=' + str(request.args.get('days', 7)),
        '/api/trades/stats',
        '/api/trades/account',
    ]
    if source == 'paper':
        jobs = ['/api/trades/positions?n=' + str(n), '/api/trades/history?n=' + str(n), '/api/trades/stats', '/api/trades/account']
    elif source == 'live' or source == 'native':
        jobs = ['/api/trades/native_positions', '/api/trades/native_history?days=' + str(request.args.get('days', 7)), '/api/trades/stats', '/api/trades/account']
    elif source == 'mt5' or source == 'live_history':
        jobs = ['/api/trades/live_history?n=' + str(n) + '&instrument=' + request.args.get('instrument','XAUUSD')]
    base = request.host_url.rstrip('/')
    agg = {'jobs': [], 'errors': []}
    for rel in jobs:
        try:
            r = requests.get(base + rel, timeout=10)
            agg['jobs'].append({'url': base + rel, 'status': r.status_code, 'body': r.json() if r.headers.get('content-type','').startswith('application/json') else r.text[:500]})
            if r.status_code >= 400:
                agg['errors'].append({'url': base + rel, 'status': r.status_code, 'body': r.text[:200]})
        except Exception as e:  # noqa: BLE001
            agg['errors'].append({'url': base + rel, 'error': str(e)})
    return jsonify(agg)


@app.route('/api/vault', methods=['GET'])
def api_vault_index():
    return redirect('/api/vault/tree')


@app.route('/api/skills', methods=['GET'])
def api_skills_json():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'skills')
    items = []
    for root, dirs, files in os.walk(base):
        for f in files:
            if f.endswith('.md'):
                rel = os.path.relpath(os.path.join(root, f), base)
                items.append({'name': rel.replace('.md','').replace(os.sep,'/'), 'path': rel})
    skills_dir = Path(os.getenv('HERMES_SKILLS_DIR', str(Path.home()/'.hermes'/'skills'/'trading')))
    if skills_dir.exists():
        for p in skills_dir.glob('*.md'):
            items.append({'name': p.stem, 'path': str(p)})
    return jsonify(items)


@app.route('/api/strategies', methods=['GET'])
def api_strategies_json():
    try:
        r = requests.get('http://127.0.0.1:8080/api/strategy/list', timeout=5)
        if r.status_code == 200:
            return jsonify(r.json())
    except Exception:
        pass
    return jsonify({"error": "strategies_unavailable"}), 503


@app.route('/api/loops', methods=['GET'])
def api_loops_json():
    state = {}
    state_path = '/data/kanban/state.json'
    try:
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                kanban = json.load(f).get('columns', {})
        else:
            kanban = {}
        state = {
            'kanban': kanban,
            'loops': {
                'subagent_board': {
                    'in_progress': len(kanban.get('in_progress', []) or []),
                    'todo': len(kanban.get('todo', []) or []),
                    'review': len(kanban.get('review', []) or []),
                    'done': len(kanban.get('done', []) or [])
                },
                'bind_mount_test': 'bind_mount_ok'
            }
        }
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify(state)


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "path": getattr(e, 'description', '')}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
