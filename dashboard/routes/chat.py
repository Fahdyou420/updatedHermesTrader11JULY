import os, json, re, requests, redis
from flask import Blueprint, request, Response, jsonify

chat_bp = Blueprint('chat', __name__)

HERMES_RPC_URL  = os.getenv("HERMES_RPC_URL", "http://host.docker.internal:7778")
OLLAMA_URL      = os.getenv("OLLAMA_URL",      "http://host.docker.internal:11434")
REDIS_URL       = os.getenv("REDIS_URL",       "redis://redis:6379")
NATIVE_API_URL  = os.getenv("NATIVE_API_URL",  "http://host.docker.internal:7779")
NOUS_API_KEY    = os.getenv("NOUS_API_KEY", "")
NOUS_MODEL      = os.getenv("NOUS_MODEL", "stepfun/step-3.7-flash:free")
NOUS_BASE_URL   = "https://inference-api.nousresearch.com/v1"

SYSTEM_PROMPT = """You are Hermes, an autonomous SMC/ICT trading agent for XAUUSD and BTCUSD.
Use Smart Money Concepts: BOS, CHoCH, Order Blocks, FVGs, liquidity sweeps.
Be precise with price levels. Max 1% risk per trade. Staged trust: hypothesis->backtest->paper->live.
CRITICAL INSTRUCTION: You MUST use tools to fetch real prices before answering ANY market or price-related questions.
Do NOT guess or use your training data for current prices.
To use a tool, output exactly this format and wait for the response:
[TOOL: read_market_bars] {"instrument": "XAUUSD", "timeframe": "M15", "n": 1} [/TOOL]

Available tools:
- read_market_bars: {"instrument": "XAUUSD", "timeframe": "M15", "n": 50} — returns OHLCV bars
- get_account_state: {} — returns MT5 balance, equity
- get_paper_trade_status: {} — returns paper trading stats"""

# ─── Tool Execution Engine ─────────────────────────────────────────────────────
def _execute_tool(tool_name: str, params: dict) -> str:
    """Executes tool calls from fallback LLM tiers by hitting the Native API directly."""
    try:
        if tool_name == "read_market_bars":
            inst = params.get("instrument", "XAUUSD")
            tf   = params.get("timeframe", "M15")
            n    = params.get("n", 10)
            r = requests.get(
                f"{NATIVE_API_URL}/api/native/latest_bars",
                params={"instrument": inst, "tf": tf, "n": n},
                timeout=8
            )
            if r.ok:
                bars = r.json()
                if isinstance(bars, list) and bars:
                    last = bars[-1]
                    return json.dumps({
                        "status": "ok",
                        "instrument": inst,
                        "latest_bar": last,
                        "current_price": last.get("close"),
                        "total_bars": len(bars)
                    })
            return json.dumps({"error": f"Native API returned {r.status_code}"})

        elif tool_name in ("get_account_state", "account_state"):
            r = requests.get(f"{NATIVE_API_URL}/api/native/account", timeout=5)
            if r.ok:
                return json.dumps(r.json())
            return json.dumps({"error": "Native API account endpoint unavailable"})

        elif tool_name == "get_paper_trade_status":
            r = requests.get("http://paper_trader:5561/stats", timeout=5)
            if r.ok:
                return json.dumps(r.json())
            return json.dumps({"error": "Paper trader unavailable"})

        else:
            # Try forwarding to hermes_rpc for registered tools
            r = requests.post(
                f"{HERMES_RPC_URL}/tool",
                json={"tool_name": tool_name, "params": params},
                timeout=15
            )
            if r.ok:
                return json.dumps(r.json())
            return json.dumps({"error": f"Tool '{tool_name}' not found"})

    except Exception as e:
        return json.dumps({"error": str(e)})


def _parse_and_execute_tools(text: str) -> list[dict]:
    """
    Parses [TOOL: name] {...} [/TOOL] and <tool_call>...</tool_call> patterns
    from LLM text output and executes each tool call.
    Returns list of {tool_name, params, result} dicts.
    """
    executions = []

    # Pattern 1: [TOOL: name] {...} [/TOOL]
    bracket_pattern = r"\[TOOL:\s*(\w+)\]\s*(\{[\s\S]*?\})\s*\[/TOOL\]"
    for m in re.finditer(bracket_pattern, text, re.IGNORECASE):
        tool_name = m.group(1).strip()
        try:
            params = json.loads(m.group(2).strip())
        except Exception:
            params = {}
        result = _execute_tool(tool_name, params)
        executions.append({"tool_name": tool_name, "params": params, "result": result})

    # Pattern 2: XML <tool_call><function=name>...</function></tool_call>
    xml_pattern = r"<tool_call>\s*<function=([\w_]+)>(.*?)</function>\s*</tool_call>"
    for m in re.finditer(xml_pattern, text, re.DOTALL | re.IGNORECASE):
        tool_name = m.group(1).strip()
        params_text = m.group(2)
        params = {}
        for pm in re.finditer(r"<parameter=([\w_]+)>(.*?)</parameter>", params_text, re.DOTALL | re.IGNORECASE):
            params[pm.group(1).strip()] = pm.group(2).strip()
        result = _execute_tool(tool_name, params)
        executions.append({"tool_name": tool_name, "params": params, "result": result})

    return executions


def _build_tool_feedback(executions: list[dict]) -> str:
    """Formats tool results as system context for the next LLM call."""
    if not executions:
        return ""
    parts = []
    for ex in executions:
        parts.append(f"[System: Tool '{ex['tool_name']}' executed → {ex['result']}]")
    return "\n".join(parts)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _discover_model():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.ok:
            models = [m["name"] for m in r.json().get("models", [])]
            for kw in ["hermes", "llama3.1", "llama3", "mistral", "qwen"]:
                for m in models:
                    if kw in m.lower():
                        return m
            if models: return models[0]
    except Exception:
        pass
    return "hermes3:latest"


def _save_history(role, content):
    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.rpush("chat_history", json.dumps({"role": role, "content": content}))
        r.ltrim("chat_history", -50, -1)
    except Exception:
        pass


# ─── Streaming Paths ──────────────────────────────────────────────────────────
def _stream_rpc(message, history):
    """Primary path: stream through hermes_rpc (has its own tool-calling engine)."""
    try:
        r = requests.post(f"{HERMES_RPC_URL}/chat",
                          json={"message": message, "task_type": "analysis",
                                "context": {"history": history[-10:]}},
                          stream=True, timeout=180)
        if r.status_code != 200:
            yield f"data: {json.dumps({'type': 'token', 'content': f'RPC error {r.status_code}'})}\\n\\n"
            yield f"data: {json.dumps({'type': 'done', 'content': ''})}\\n\\n"
            return
        accumulated = ""
        for line in r.iter_lines():
            if not line: continue
            decoded = line.decode("utf-8") if isinstance(line, bytes) else line
            if decoded.startswith("data:"): decoded = decoded[5:].strip()
            try:
                obj = json.loads(decoded)
                if obj.get("type") == "token" and obj.get("content"):
                    accumulated += obj["content"]
                yield f"data: {json.dumps(obj)}\\n\\n"
                if obj.get("type") == "done": break
            except json.JSONDecodeError:
                if decoded and decoded != "[DONE]":
                    accumulated += decoded
                    yield f"data: {json.dumps({'type':'token','content':decoded})}\\n\\n"
        if accumulated.strip(): _save_history("assistant", accumulated)
        yield f"data: {json.dumps({'type':'done','content':''})}\\n\\n"
    except requests.exceptions.ConnectionError:
        yield from _stream_nous_direct(message, history)
    except Exception as e:
        yield f"data: {json.dumps({'type':'token','content':f'Error: {e}'})}\\n\\n"
        yield f"data: {json.dumps({'type':'done','content':''})}\\n\\n"


def _stream_nous_direct(message, history):
    """Tier-2 fallback: direct Nous Portal call with tool execution loop."""
    if not NOUS_API_KEY:
        yield from _stream_ollama_direct(message, history)
        return

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-10:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})

    max_tool_rounds = 3
    for _round in range(max_tool_rounds):
        try:
            r = requests.post(
                f"{NOUS_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {NOUS_API_KEY}", "Content-Type": "application/json"},
                json={"model": NOUS_MODEL, "messages": messages, "stream": False},
                timeout=120,
            )
            if r.status_code == 200:
                text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if text:
                    executions = _parse_and_execute_tools(text)
                    if executions:
                        # Tool was called — inject result and loop
                        tool_feedback = _build_tool_feedback(executions)
                        yield f"data: {json.dumps({'type':'token','content':text})}\\n\\n"
                        yield f"data: {json.dumps({'type':'token','content': chr(10) + tool_feedback + chr(10)})}\\n\\n"
                        messages.append({"role": "assistant", "content": text})
                        messages.append({"role": "user", "content": f"Tool results: {tool_feedback}\\nNow answer the original question using the real data above."})
                        continue  # re-call LLM with tool results
                    else:
                        # Final answer — no tools called
                        _save_history("assistant", text)
                        yield f"data: {json.dumps({'type':'token','content':text})}\\n\\n"
                        yield f"data: {json.dumps({'type':'done','content':''})}\\n\\n"
                        return
        except Exception:
            pass
        break

    # Nous failed entirely — fall through
    yield from _stream_ollama_direct(message, history)


def _stream_ollama_direct(message, history):
    """Tier-3 fallback: direct Ollama call with tool execution loop."""
    model = _discover_model()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-10:]:
        messages.append({"role": h.get("role","user"), "content": h.get("content","")})
    messages.append({"role": "user", "content": message})

    max_tool_rounds = 3
    for _round in range(max_tool_rounds):
        accumulated = ""
        tool_yielded = False
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat",
                              json={"model": model, "messages": messages, "stream": True},
                              stream=True, timeout=180)
            if not r.ok:
                yield f"data: {json.dumps({'type':'token','content':f'Ollama {r.status_code}: {r.text[:200]}'})}\\n\\n"
                yield f"data: {json.dumps({'type':'done','content':''})}\\n\\n"
                return
            for line in r.iter_lines():
                if not line: continue
                try:
                    obj = json.loads(line)
                    token = obj.get("message", {}).get("content", "")
                    if token:
                        accumulated += token
                        yield f"data: {json.dumps({'type':'token','content':token})}\\n\\n"
                    if obj.get("done"): break
                except json.JSONDecodeError:
                    pass

            # Check for tool calls in completed response
            executions = _parse_and_execute_tools(accumulated)
            if executions:
                tool_feedback = _build_tool_feedback(executions)
                yield f"data: {json.dumps({'type':'token','content': chr(10) + tool_feedback + chr(10)})}\\n\\n"
                messages.append({"role": "assistant", "content": accumulated})
                messages.append({"role": "user", "content": f"Tool results: {tool_feedback}\\nNow answer the original question using the real data above."})
                tool_yielded = True
                continue  # re-run with results

        except Exception as e:
            yield f"data: {json.dumps({'type':'token','content':f'Ollama unreachable: {e}'})}\\n\\n"
            yield f"data: {json.dumps({'type':'done','content':''})}\\n\\n"
            return

        # No tools called — final answer
        if accumulated.strip(): _save_history("assistant", accumulated)
        yield f"data: {json.dumps({'type':'done','content':''})}\\n\\n"
        return

    # Exhausted tool rounds
    yield f"data: {json.dumps({'type':'done','content':''})}\\n\\n"


# ─── Routes ───────────────────────────────────────────────────────────────────
@chat_bp.route('/send', methods=['POST'])
def send_message():
    data    = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message: return jsonify({"error": "No message"}), 400
    _save_history("user", message)
    history = []
    try:
        rc = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        history = [json.loads(h) for h in rc.lrange("chat_history", 0, -1)]
    except Exception: pass
    return Response(_stream_rpc(message, history), mimetype="text/event-stream",
                    headers={"Cache-Control":"no-cache","Connection":"keep-alive","X-Accel-Buffering":"no"})


@chat_bp.route('/history', methods=['GET'])
def get_history():
    try:
        rc = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        return jsonify([json.loads(h) for h in rc.lrange("chat_history", 0, -1)])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route('/models', methods=['GET'])
def get_models():
    ollama_models = []
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.ok:
            ollama_models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return jsonify({
        "llm_chain": ["hermes_rpc (Nous→Gemini→Ollama)", "direct-Nous (tool-loop)", "direct-Ollama (tool-loop)"],
        "active_model": NOUS_MODEL if NOUS_API_KEY else _discover_model(),
        "nous": {"model": NOUS_MODEL, "configured": bool(NOUS_API_KEY)},
        "ollama": {"models": ollama_models, "selected": _discover_model()},
    })
