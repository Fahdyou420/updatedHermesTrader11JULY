import json, os, glob, shutil
from datetime import datetime

MT5_COMMON = r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\Common\Files"
BUS_DIR = os.path.join(MT5_COMMON, "bus") if os.path.isdir(os.path.join(MT5_COMMON, "bus")) else MT5_COMMON
HISTORY_DIR = MT5_COMMON
EMERGENCY_DD = 0.045
RISK_PER_TRADE = 0.01


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def list_bus_messages():
    return sorted(glob.glob(os.path.join(BUS_DIR, "*signal*.*")) + glob.glob(os.path.join(BUS_DIR, "*.signal.*")))


def main():
    log_path = os.path.join("C:\\Users\\user\\Desktop\\hermes_claude\\omni-core\\validators", "logs", "master_validator.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    state_path = os.path.join("C:\\Users\\user\\Desktop\\hermes_claude\\omni-core\\validators", "memory", "state.json")
    ms_path = os.path.join(MT5_COMMON, "OmniVision_Feed.json")
    ai_cmd = os.path.join(MT5_COMMON, "AI_Command.json")

    ms = read_json(ms_path)
    state = read_json(state_path)
    now = datetime.utcnow().isoformat() + "Z"

    account = ms.get("account") or {}
    equity = float(account.get("equity") or ms.get("equity") or 0.0)
    balance = float(account.get("balance") or ms.get("balance") or 0.0)
    daily_pnl = float(ms.get("daily_pnl") or account.get("profit") or 0.0)
    if balance > 0 and daily_pnl != 0:
        daily_loss_pct = max(0.0, -daily_pnl) / balance
    else:
        daily_loss_pct = 0.0

    state["last_run"] = now
    state["daily_loss_pct"] = daily_loss_pct

    cmd = {
        "timestamp": now,
        "symbol": ms.get("symbol", "XAUUSD"),
        "timeframe": ms.get("timeframe", "M15"),
        "direction": None,
        "price_cluster": None,
        "confluence_count": 0,
        "confluence_sources": [],
        "daily_open": ms.get("daily_open"),
        "amd_pass": False,
        "risk_per_trade": RISK_PER_TRADE,
        "emergency_halt": False,
        "drawing_objects": [],
        "description": "",
        "trade_ticket": None,
        "status": "pending_validation",
        "source_bus": BUS_DIR,
        "validator": "master_validator_v1",
    }

    if daily_loss_pct >= EMERGENCY_DD:
        cmd["emergency_halt"] = True
        cmd["status"] = "emergency_halt"
        cmd["description"] = f"Daily loss {daily_loss_pct:.2%} reached emergency threshold {EMERGENCY_DD:.2%}. Halt execution."
        write_json(ai_cmd, cmd)
        write_json(state_path, state)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{now} EMERGENCY_HALT daily_loss={daily_loss_pct:.4f}\n")
        print(json.dumps(cmd, indent=2))
        return

    daily_open = float(ms.get("daily_open") or 0.0)
    ask = float(ms.get("ask") or 0.0)
    bid = float(ms.get("bid") or 0.0)
    symbol = ms.get("symbol", "XAUUSD")
    state["symbol"] = symbol
    state["daily_open"] = daily_open
    state["ask"] = ask
    state["bid"] = bid

    cmd["symbol"] = symbol
    cmd["daily_open"] = daily_open

    if daily_open <= 0.0 or ask <= 0.0 or bid <= 0.0:
        cmd["status"] = "awaiting_market_state_feed"
        cmd["description"] = "OmniVision_Feed.json has no live pricing fields; AMD filter cannot run."
        write_json(ai_cmd, cmd)
        write_json(state_path, state)
        print(json.dumps(cmd, indent=2))
        return

    clusters = {}
    for p in list_bus_messages():
        data = read_json(p)
        text = data.get("message") or data.get("signal") or data.get("content") or ""
        if not text and isinstance(data, dict):
            text = json.dumps(data)
        if "[SIGNAL]" in str(text):
            price = None
            try:
                import re
                mm = re.search(r"at\s+([0-9]+(?:\.[0-9]+)?)", str(text))
                if mm:
                    price = float(mm.group(1))
            except Exception:
                pass
            if price is None:
                continue
            clusters.setdefault(round(price, 2), []).append({"path": p, "message": str(text)})

    best = None
    for price, items in clusters.items():
        uniq = []
        for it in items:
            tag = "unknown"
            import re
            mm = re.search(r"Agent\s+(\d+)", it["message"])
            if mm:
                tag = f"agent_{mm.group(1)}"
            if tag not in uniq:
                uniq.append(tag)
        if len(uniq) >= 3:
            best = {"price": price, "agents": uniq, "items": items}
            break

    if best:
        price_cluster = best["price"]
        if ask > 0 and bid > 0:
            if ask < daily_open:
                direction = "BUY"
                amd_pass = True
            elif bid > daily_open:
                direction = "SELL"
                amd_pass = True
            else:
                direction = None
                amd_pass = False
        else:
            direction = None
            amd_pass = False

        if direction and amd_pass:
            rect = {
                "type": "OBJ_RECTANGLE",
                "name": "OmniVision_OB",
                "window": 0,
                "time": 0,
                "price1": price_cluster - 1.0,
                "price2": price_cluster + 1.0,
                "color": "clrGreen" if direction == "BUY" else "clrRed",
                "style": "STYLE_SOLID",
                "width": 1,
                "selectable": True,
                "hidden": False,
                "back": True,
                "zorder": 0,
                "mql5_object": "OBJ_RECTANGLE",
            }
            hline = {
                "type": "OBJ_HLINE",
                "name": "OmniVision_Level",
                "window": 0,
                "time": 0,
                "price": price_cluster,
                "color": "clrYellow",
                "style": "STYLE_DASH",
                "width": 1,
                "selectable": True,
                "hidden": False,
                "back": True,
                "zorder": 0,
                "mql5_object": "OBJ_HLINE",
            }
            txt = {
                "type": "OBJ_TEXT",
                "name": "OmniVision_Label",
                "window": 0,
                "time": 0,
                "price": price_cluster + 1.5,
                "text": f"OmniVision {direction} @ {price_cluster:.2f}",
                "font_size": 10,
                "color": "clrWhite",
                "style": "STYLE_NOBORDER",
                "back": True,
                "selectable": True,
                "hidden": False,
                "zorder": 0,
                "mql5_object": "OBJ_TEXT",
            }
            cmd["direction"] = direction
            cmd["price_cluster"] = price_cluster
            cmd["confluence_count"] = len(best["agents"])
            cmd["confluence_sources"] = best["agents"]
            cmd["amd_pass"] = True
            cmd["drawing_objects"] = [rect, hline, txt]
            cmd["status"] = "validated"
            cmd["description"] = f"Validated {direction} at {price_cluster:.2f} from {len(best['agents'])} sources."
        else:
            cmd["status"] = "blocked_amd"
            cmd["description"] = "AMD daily-open filter blocked entry."
            if best["agents"]:
                cmd["confluence_sources"] = best["agents"]
                cmd["confluence_count"] = len(best["agents"])
                cmd["price_cluster"] = price_cluster
    else:
        cmd["status"] = "pending_validation"

    write_json(ai_cmd, cmd)
    write_json(state_path, state)
    print(json.dumps(cmd, indent=2))


if __name__ == "__main__":
    main()
