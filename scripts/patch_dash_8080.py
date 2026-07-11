import os, sys

APP_ROOT = "/app"
DATA_DIR = "/data"
OBSIDIAN_DIR = "/data/obsidian"

TRADES_PATCH = """import os
import json
import requests
import redis
from flask import Blueprint, request, Response, jsonify

trades_bp = Blueprint('trades', __name__)

PAPER_TRADER_URL = os.getenv("PAPER_TRADER_URL", "http://paper_trader:5561")
MT5_BRIDGE_URL    = os.getenv("MT5_BRIDGE_URL", "http://mt5_bridge:5558")
NATIVE_MT5_URL    = os.getenv("NATIVE_MT5_URL", "http://host.docker.internal:7779")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
TRADES_DATA_DIR = os.getenv("TRADES_DATA_DIR", "/data/trades")
EXECUTION_URL = os.getenv("EXECUTION_URL", "http://execution:5563")

os.makedirs(TRADES_DATA_DIR, exist_ok=True)

def read_last_lines_jsonl(filepath, limit=50):
    if not os.path.exists(filepath):
        return []
    records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        take_lines = lines[-limit:] if len(lines) > limit else lines
        for line in take_lines:
            line_str = line.strip()
            if line_str:
                try:
                    records.append(json.loads(line_str))
                except Exception:
                    pass
    except Exception as e:
        print(f"Failed parsing jsonl log {filepath}: {e}")
    records.reverse()
    return records

def _normalize_trade(t, source="unknown", status="OPEN", closed_at=""):
    if isinstance(t, dict):
        return {
            "id": str(t.get("id") or t.get("ticket") or t.get("signal_id") or ""),
            "timestamp": str(t.get("timestamp") or t.get("open_time") or ""),
            "instrument": str(t.get("instrument") or t.get("symbol") or "XAUUSD"),
            "direction": str(t.get("direction") or t.get("side") or "").upper(),
            "type": str(t.get("setup_type") or t.get("type") or ""),
            "entryPrice": float(t.get("entry_price") or t.get("entryPrice") or 0),
            "exitPrice": float(t.get("close_price") or t.get("exitPrice") or 0),
            "stopLoss": float(t.get("sl") or t.get("stopLoss") or 0),
            "takeProfit": float(t.get("tp") or t.get("takeProfit") or 0),
            "lotSize": float(t.get("lots") or t.get("lotSize") or 0),
            "currentPrice": float(t.get("current_price") or t.get("currentPrice") or t.get("close_price") or 0),
            "pnl": float(t.get("profit") or t.get("pnl") or 0),
            "status": str(t.get("status") or status),
            "stage": str(t.get("mode") or t.get("stage") or ""),
            "riskPercent": float(t.get("risk_pct") or t.get("riskPercent") or 0),
            "rrRatio": float(t.get("r_ratio") or t.get("rrRatio") or 0),
            "closedAt": str(t.get("close_time") or closed_at),
            "notes": str(t.get("agent_notes") or t.get("notes") or ""),
            "source": source,
        }
    return {"error": "invalid trade", "raw": str(t)}

@trades_bp.route('/positions', methods=['GET'])
def get_positions():
    combined = []
    try:
        res = requests.get(f\"{PAPER_TRADER_URL}/positions\", timeout=5)
        paper = res.json() if res.ok else []
        for p in paper:
            p["source"] = "paper"
            p["stage"] = p.get("mode", "paper")
        combined.extend(paper)
    except Exception as e:
        print(f"Paper Trader offline: {e}")

    try:
        res = requests.get(f\"{NATIVE_MT5_URL}/api/native/positions\", timeout=10)
        if res.ok:
            data = res.json()
            positions = data.get("positions", [])
            for p in positions:
                p["source"] = "native"
                p["mode"] = "live"
            combined.extend(positions)
            return jsonify(combined)
    except Exception as e:
        print(f"Native MT5 positions unavailable: {e}")

    try:
        res = requests.get(f\"{MT5_BRIDGE_URL}/positions\", timeout=5)
        live = res.json() if res.ok else []
        for p in live:
            p["source"] = "zmq_bridge"
            p["mode"] = "live"
        combined.extend(live)
    except Exception as e:
        print(f"MT5 bridge positions unavailable: {e}")

    return jsonify(combined)


@trades_bp.route('/account', methods=['GET'])
def get_account():
    try:
        res = requests.get(f\"{NATIVE_MT5_URL}/api/native/account\", timeout=10)
        if res.ok:
            data = res.json()
            if not data.get("error"):
                data["source"] = "native"
                return jsonify(data)
    except Exception as e:
        print(f"Native MT5 account unavailable, falling back to ZMQ: {e}")

    try:
        res = requests.get(f\"{MT5_BRIDGE_URL}/account_state\", timeout=5)
        data = res.json() if res.ok else {}
        data["source"] = "zmq_bridge"
        return jsonify(data)
    except Exception as e:
        print(f"MT5 bridge account_state also unavailable: {e}")
        return jsonify({"balance": 0, "equity": 0, "margin": 0, "profit": 0, "source": "unavailable"})


@trades_bp.route('/history', methods=['GET'])
def get_history():
    try:
        res = requests.get(f\"{PAPER_TRADER_URL}/history?n=50\", timeout=10)
        if res.ok:
            data = res.json()
            if isinstance(data, list):
                return jsonify([_normalize_trade(x, source="paper", status="CLOSED") for x in data])
            return jsonify(data)
    except Exception as e:
        print(f"Paper Trader offline: {e}")
    return jsonify([])


@trades_bp.route('/stats', methods=['GET'])
def get_stats():
    stats = {
        "balance": 0.0, "equity": 0.0, "win_rate": 0.0,
        "total_trades": 0, "profit_factor": 0.0,
        "max_drawdown_percent": 0.0, "net_profit": 0.0, "net_r": 0.0
    }
    try:
        res = requests.get(f\"{PAPER_TRADER_URL}/stats\", timeout=10)
        if res.ok:
            stats.update(res.json())
    except Exception as e:
        print(f"Paper Trader offline: {e}")

    acc = None
    try:
        res = requests.get(f\"{NATIVE_MT5_URL}/api/native/account\", timeout=10)
        if res.ok:
            acc = res.json()
    except Exception:
        pass

    if not acc or acc.get("error"):
        try:
            res = requests.get(f\"{MT5_BRIDGE_URL}/account_state\", timeout=5)
            if res.ok:
                acc = res.json()
        except Exception as e:
            print(f"Both native and ZMQ account unavailable: {e}")

    if acc and not acc.get("error"):
        if acc.get("balance"):
            stats["balance"] = acc["balance"]
        if acc.get("equity"):
            stats["equity"] = acc["equity"]
        if acc.get("profit"):
            stats["net_profit"] = acc["profit"]

    return jsonify(stats)


@trades_bp.route('/signals/approved', methods=['GET'])
def get_approved_signals():
    filepath = os.path.join(TRADES_DATA_DIR, "approved_signals.jsonl")
    records = read_last_lines_jsonl(filepath, limit=50)
    return jsonify(records)


@trades_bp.route('/signals/rejected', methods=['GET'])
def get_rejected_signals():
    filepath = os.path.join(TRADES_DATA_DIR, "rejected_signals.jsonl")
    records = read_last_lines_jsonl(filepath, limit=50)
    return jsonify(records)


@trades_bp.route('/candidates', methods=['GET'])
def get_candidates():
    try:
        res = requests.get(f\"{PAPER_TRADER_URL}/promotion_candidates\", timeout=10)
        if res.ok:
            return jsonify(res.json())
    except Exception as e:
        print(f"Paper Trader offline: {e}")
    return jsonify([])


@trades_bp.route('/live_history', methods=['GET'])
def get_live_broker_history():
    n = int(request.args.get('n', 100))
    days = int(request.args.get('days', 30))
    instrument = request.args.get('instrument', '')

    try:
        res = requests.get(f\"{NATIVE_MT5_URL}/api/native/history\", params={'days': days, 'instrument': instrument}, timeout=20)
        if res.ok:
            data = res.json()
            trades = data.get("trades", [])
            if instrument:
                trades = [t for t in trades if str(t.get('symbol', '')).upper() == instrument.upper()]
            trades = trades[-n:] if len(trades) > n else trades
            return jsonify(trades)
    except Exception as e:
        print(f"Native MT5 history unavailable: {e}")

    try:
        res = requests.get(f\"{MT5_BRIDGE_URL}/live_history\", params={'n': n, 'instrument': instrument}, timeout=20)
        deals = res.json() if res.ok else []
        return jsonify(deals)
    except Exception as e:
        print(f"MT5 bridge live_history also unavailable: {e}")
        return jsonify([])


@trades_bp.route('/native_positions', methods=['GET'])
def get_native_positions():
    symbol = request.args.get('symbol', '')
    try:
        params = {'symbol': symbol} if symbol else {}
        res = requests.get(f\"{NATIVE_MT5_URL}/api/native/positions\", params=params, timeout=15)
        if res.ok:
            data = res.json()
            positions = data.get("positions", [])
            return jsonify(positions)
    except Exception as e:
        print(f"Native MT5 positions unavailable: {e}")
    return jsonify([])


@trades_bp.route('/native_account', methods=['GET'])
def get_native_account():
    try:
        res = requests.get(f\"{NATIVE_MT5_URL}/api/native/account\", timeout=15)
        if res.ok:
            return jsonify(res.json())
    except Exception as e:
        print(f"Native MT5 account unavailable: {e}")
    return jsonify({"error": "unavailable"})


@trades_bp.route('/native_history', methods=['GET'])
def get_native_history():
    n = int(request.args.get('n', 100))
    days = int(request.args.get('days', 7))
    instrument = request.args.get('instrument', '')
    try:
        res = requests.get(f\"{NATIVE_MT5_URL}/api/native/history\", params={'days': days, 'instrument': instrument}, timeout=15)
        if res.ok:
            data = res.json()
            trades = data.get("trades", [])
            if instrument:
                trades = [t for t in trades if str(t.get('symbol', '')).upper() == instrument.upper()]
            trades = trades[-n:] if len(trades) > n else trades
            return jsonify(trades)
    except Exception as e:
        print(f"Native MT5 history unavailable: {e}")
    return jsonify([])


@trades_bp.route('/close', methods=['GET'])
def fallback_close():
    return jsonify({"error": "use /native_positions and native close endpoint from MCP"}), 405


@trades_bp.route('/draw', methods=['GET'])
def fallback_draw():
    return jsonify({"error": "draw endpoint unavailable"}), 404


@trades_bp.route('/kill', methods=['POST', 'GET'])
def trigger_kill():
    flatten = request.args.get('flatten', 'false').lower() == 'true'
    try:
        res = requests.post(f\"{EXECUTION_URL}/kill?flatten={str(flatten).lower()\", timeout=10)
        return jsonify(res.json() if res.ok else {"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@trades_bp.route('/resume', methods=['POST', 'GET'])
def trigger_resume():
    try:
        res = requests.post(f\"{EXECUTION_URL}/resume\", timeout=10)
        return jsonify(res.json() if res.ok else {"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@trades_bp.route('/reset', methods=['POST', 'GET'])
def trigger_reset():
    try:
        res = requests.post(f\"{PAPER_TRADER_URL}/reset\", timeout=10)
        return jsonify(res.json() if res.ok else {"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@trades_bp.route('/pending', methods=['GET'])
def get_pending_signals():
    try:
        res = requests.get(f\"{EXECUTION_URL}/pending_signals\", timeout=10)
        return jsonify(res.json() if res.ok else []), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@trades_bp.route('/pending/<signal_id>/approve', methods=['POST', 'GET'])
def approve_signal(signal_id):
    try:
        res = requests.post(f\"{EXECUTION_URL}/signal/{signal_id}/approve\", timeout=15)
        return jsonify(res.json() if res.ok else {"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@trades_bp.route('/pending/<signal_id>/reject', methods=['POST', 'GET'])
def reject_signal(signal_id):
    try:
        res = requests.post(f\"{EXECUTION_URL}/signal/{signal_id}/reject\", timeout=15)
        return jsonify(res.json() if res.ok else {"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@trades_bp.route('/approve', methods=['POST', 'GET'])
def approve_first():
    try:
        res = requests.get(f\"{EXECUTION_URL}/pending_signals\", timeout=10)
        pending = res.json() if res.ok else []
    except Exception as e:
        return jsonify({"error": f"pending fetch failed: {e}"}), 500
    if not pending:
        return jsonify({"error": "No pending signals"}), 404
    signal_id = pending[0].get("signal_id") or pending[0].get("id")
    return approve_signal(signal_id)


@trades_bp.route('/reject', methods=['POST', 'GET'])
def reject_first():
    try:
        res = requests.get(f\"{EXECUTION_URL}/pending_signals\", timeout=10)
        pending = res.json() if res.ok else []
    except Exception as e:
        return jsonify({"error": f"pending fetch failed: {e}"}), 500
    if not pending:
        return jsonify({"error": "No pending signals"}), 404
    signal_id = pending[0].get("signal_id") or pending[0].get("id")
    return reject_signal(signal_id)

"""

def joinp(*parts):
    return "/".join(parts)

APP_ROOT = "/app"
...
write_file(joinp(APP_ROOT, "dashboard", "routes", "trades.py"), TRADES_PATCH)
chmod_exec(joinp(APP_ROOT, "dashboard", "routes", "trades.py"))
