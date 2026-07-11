import os, json, requests, redis as redis_lib
from flask import Blueprint, request, Response, jsonify

trades_bp = Blueprint('trades', __name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
NATIVE_MT5_URL = os.getenv("NATIVE_MT5_URL", "http://host.docker.internal:7779")
PAPER_TRADER_URL = os.getenv("PAPER_TRADER_URL", "http://paper_trader:5561")
EXECUTION_URL = os.getenv("EXECUTION_URL", "http://execution:5563")
TRADES_DATA_DIR = os.getenv("TRADES_DATA_DIR", "/data/trades")
os.makedirs(TRADES_DATA_DIR, exist_ok=True)


def _norm(t, source, status="OPEN", closed_at=""):
    if not isinstance(t, dict):
        return {"error": "invalid trade"}
    direction = str(
        t.get("direction")
        or t.get("side")
        or t.get("type", "")
        or ""
    ).upper()
    if direction not in {"BUY", "SELL"}:
        direction = ""
    return {
        "id": str(t.get("id") or t.get("ticket") or t.get("signal_id") or ""),
        "timestamp": str(t.get("timestamp") or t.get("open_time") or ""),
        "instrument": str(t.get("instrument") or t.get("symbol") or "XAUUSD").upper(),
        "direction": direction,
        "type": str(t.get("setup_type") or t.get("type") or ""),
        "entryPrice": float(t.get("entry_price") or t.get("entryPrice") or t.get("price_open", 0) or 0),
        "exitPrice": float(t.get("close_price") or t.get("exitPrice") or t.get("price_current") or t.get("close_price", 0) or 0),
        "stopLoss": float(t.get("sl") or t.get("stopLoss") or 0),
        "takeProfit": float(t.get("tp") or t.get("takeProfit") or 0),
        "lotSize": float(t.get("lots") or t.get("lotSize") or 0),
        "currentPrice": float(t.get("current_price") or t.get("currentPrice") or t.get("price_current") or t.get("close_price", 0) or 0),
        "pnl": float(t.get("profit") or t.get("pnl") or 0),
        "status": str(t.get("status") or status).upper(),
        "stage": str(t.get("mode") or t.get("stage") or ""),
        "riskPercent": float(t.get("risk_pct") or t.get("riskPercent") or 0),
        "rrRatio": float(t.get("r_ratio") or t.get("rrRatio") or 0),
        "closedAt": str(t.get("close_time") or closed_at),
        "notes": str(t.get("agent_notes") or t.get("notes") or ""),
        "source": source,
    }


def _http_get_json(url, timeout=15, params=None):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print(f"HTTP GET failed {url}: {e}")
        return None


@trades_bp.route('/positions', methods=['GET'])
def get_positions():
    combined = []
    try:
        data = _http_get_json(f"{PAPER_TRADER_URL}/positions", timeout=8) or []
        if isinstance(data, list):
            for p in data:
                p["source"] = "paper"
                p["mode"] = p.get("mode", "paper")
            combined.extend(data)
    except Exception as e:
        print(f"Paper positions failed: {e}")
    try:
        data = _http_get_json(f"{NATIVE_MT5_URL}/positions", timeout=10)
        if data:
            positions = data.get("positions", []) if isinstance(data, dict) else data
            combined.extend([
                {"source": "native", "mode": "live", **p} if isinstance(p, dict) else p
                for p in positions
            ])
    except Exception as e:
        print(f"Native positions failed: {e}")
    return jsonify(combined)


@trades_bp.route('/history', methods=['GET'])
def get_history():
    try:
        data = _http_get_json(f"{PAPER_TRADER_URL}/history?n=100", timeout=10) or []
        if isinstance(data, list):
            return jsonify([_norm(x, source="paper", status="CLOSED") for x in data])
        return jsonify(data if isinstance(data, list) else [])
    except Exception as e:
        print(f"Paper history failed: {e}")
    return jsonify([])


@trades_bp.route('/live_history', methods=['GET'])
def live_history():
    n = int(request.args.get('n', 100))
    days = int(request.args.get('days', 30))
    instrument = (request.args.get('instrument') or '').upper()
    try:
        data = _http_get_json(
            f"{NATIVE_MT5_URL}/history",
            params={"days": days, "instrument": instrument},
            timeout=20,
        )
        if data:
            trades = data.get("trades", []) if isinstance(data, dict) else data
            if instrument:
                trades = [t for t in trades if str(t.get('symbol', '')).upper() == instrument]
            trades = trades[-n:] if len(trades) > n else trades
            return jsonify(trades)
    except Exception as e:
        print(f"Native live_history failed: {e}")
    return jsonify([])


@trades_bp.route('/native_positions', methods=['GET'])
def native_positions():
    symbol = request.args.get('symbol', '')
    params = {'symbol': symbol} if symbol else {}
    data = _http_get_json(f"{NATIVE_MT5_URL}/positions", params=params, timeout=15)
    if data:
        return jsonify(data.get("positions", []) if isinstance(data, dict) else data)
    return jsonify([])


@trades_bp.route('/native_account', methods=['GET'])
def native_account():
    data = _http_get_json(f"{NATIVE_MT5_URL}/account", timeout=10)
    if data and "error" not in data:
        return jsonify(data)
    return jsonify({"balance": 0, "equity": 0, "source": "unavailable"})


@trades_bp.route('/native_history', methods=['GET'])
def native_history():
    n = int(request.args.get('n', 100))
    days = int(request.args.get('days', 7))
    instrument = (request.args.get('instrument') or '').upper()
    data = _http_get_json(
        f"{NATIVE_MT5_URL}/history",
        params={"days": days, "instrument": instrument},
        timeout=20,
    )
    if data:
        trades = data.get("trades", []) if isinstance(data, dict) else data
        if instrument:
            trades = [t for t in trades if str(t.get('symbol', '')).upper() == instrument]
        trades = trades[-n:] if len(trades) > n else trades
        return jsonify(trades)
    return jsonify([])


@trades_bp.route('/stats', methods=['GET'])
def get_stats():
    stats = {"balance": 0.0, "equity": 0.0, "win_rate": 0.0, "total_trades": 0, "profit_factor": 0.0, "max_drawdown_percent": 0.0, "net_profit": 0.0, "net_r": 0.0}
    try:
        data = _http_get_json(f"{PAPER_TRADER_URL}/stats", timeout=10)
        if data:
            stats.update(data)
    except Exception as e:
        print(f"Paper stats unavailable: {e}")
    acc = _http_get_json(f"{NATIVE_MT5_URL}/account", timeout=10)
    if acc and "error" not in acc:
        if acc.get("balance") is not None:
            stats["balance"] = acc["balance"]
        if acc.get("equity") is not None:
            stats["equity"] = acc["equity"]
        if acc.get("profit") is not None:
            stats["net_profit"] = acc["profit"]
    return jsonify(stats)


@trades_bp.route('/account', methods=['GET'])
def get_account():
    data = _http_get_json(f"{NATIVE_MT5_URL}/account", timeout=10)
    if data:
        return jsonify(data)
    return jsonify({"balance": 0, "equity": 0, "margin": 0, "profit": 0, "source": "unavailable"})


@trades_bp.route('/pending', methods=['GET'])
def get_pending_signals():
    data = _http_get_json(f"{EXECUTION_URL}/pending_signals", timeout=10)
    if data is not None:
        if isinstance(data, list):
            return jsonify(data)
        return jsonify(data)
    return jsonify([])


@trades_bp.route('/pending/<signal_id>/approve', methods=['POST', 'GET'])
def approve_signal(signal_id):
    data = _http_get_json(f"{EXECUTION_URL}/signal/{signal_id}/approve", timeout=15)
    if data is not None:
        if isinstance(data, dict) and "error" in data:
            return jsonify(data), 400
        return jsonify(data)
    return jsonify({"error": "execution service unreachable"}), 500


@trades_bp.route('/pending/<signal_id>/reject', methods=['POST', 'GET'])
def reject_signal(signal_id):
    data = _http_get_json(f"{EXECUTION_URL}/signal/{signal_id}/reject", timeout=15)
    if data is not None:
        if isinstance(data, dict) and "error" in data:
            return jsonify(data), 400
        return jsonify(data)
    return jsonify({"error": "execution service unreachable"}), 500


@trades_bp.route('/stream', methods=['GET'])
def stream_trades():
    def event_generator():
        pubsub = None
        try:
            r = redis_lib.Redis.from_url(REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            pubsub.subscribe("PAPER_TRADE_UPDATE", "TRADE_OPENED", "TRADE_CLOSED", "TRADE_STATS", "SCHEDULER_EVENT", "KANBAN_EVENT")
            yield f"data: {json.dumps({'event': 'connected', 'message': 'Subscribed to Hermes trade event broker'})}\n\n"
            for message in pubsub.listen():
                if not message or message['type'] != 'message':
                    continue
                channel_name = message['channel']
                payload = message['data']
                try:
                    parsed = json.loads(payload)
                except Exception:
                    parsed = {"raw": payload}
                yield f"data: {json.dumps({'event': channel_name, 'data': parsed})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
        finally:
            if pubsub:
                try:
                    pubsub.unsubscribe()
                except Exception:
                    pass

    return Response(event_generator(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no'
    })


def _proxy(url, extra_json=None):
    try:
        payload = extra_json or {}
        r = requests.post(url, json=payload, timeout=10)
        return jsonify(r.json() if r.ok else {"error": r.text}), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@trades_bp.route('/kill', methods=['POST', 'GET'])
def trigger_kill():
    flatten = str(request.args.get('flatten', 'false')).lower() == "true"
    return _proxy(f"{EXECUTION_URL}/kill", {"flatten": str(flatten).lower()})


@trades_bp.route('/resume', methods=['POST', 'GET'])
def trigger_resume():
    return _proxy(f"{EXECUTION_URL}/resume")


@trades_bp.route('/reset', methods=['POST', 'GET'])
def trigger_reset():
    return _proxy(f"{PAPER_TRADER_URL}/reset")
