import datetime as d  # noqa: F401 — preserves prior alias usage if any
import json, os, time, glob
from pathlib import Path
import MetaTrader5 as mt5

SIGNAL_DIR = Path(__file__).with_suffix("").parent / "approved_signals"
SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = Path(__file__).with_suffix("").parent / "execution_operator.log"
STATE_FILE = Path(__file__).with_suffix("").parent / "execution_operator.state.json"
SYMBOL = "XAUUSD"
MAX_DAILY_DRAWDOWN_USD = -2000.0

MAGIC = 123456

def d_date() -> str:
    return datetime.date.today().isoformat()


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")


def load_state():
    default = {"date": d_date(), "day_start_equity": None, "halted": False}
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if data.get("date") != default["date"]:
                return default
            return data
        except Exception:
            return default
    return default


def save_state(state):
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        log(f"state_write_failed {e}")


def equity():
    acc = mt5.account_info()
    return float(acc.equity) if acc else 0.0


def send_native_order_via_mcp(order: dict):
    payload = {
        "action": order.get("action", "BUY"),
        "symbol": order.get("symbol", "XAUUSD"),
        "volume": float(order.get("volume", 0.1)),
        "sl": float(order.get("sl", 0.0) or 0.0),
        "tp": float(order.get("tp", 0.0) or 0.0),
        "entry_price": order.get("entry_price"),
        "comment": order.get("comment", "execution_operator"),
        "ticket": int(order.get("ticket", 0)),
    }
    # Use direct MT5 order path if MCP mapped publish fails later.
    return payload


def place_direct(order: dict):
    action_map = {
        "BUY": (mt5.TRADE_ACTION_DEAL, mt5.ORDER_TYPE_BUY),
        "SELL": (mt5.TRADE_ACTION_DEAL, mt5.ORDER_TYPE_SELL),
        "BUY_LIMIT": (mt5.TRADE_ACTION_PENDING, mt5.ORDER_TYPE_BUY_LIMIT),
        "SELL_LIMIT": (mt5.TRADE_ACTION_PENDING, mt5.ORDER_TYPE_SELL_LIMIT),
        "BUY_STOP": (mt5.TRADE_ACTION_PENDING, mt5.ORDER_TYPE_BUY_STOP),
        "SELL_STOP": (mt5.TRADE_ACTION_PENDING, mt5.ORDER_TYPE_SELL_STOP),
    }
    act, kind = action_map[order["action"]]
    price = order.get("entry_price")
    if act == mt5.TRADE_ACTION_DEAL:
        tick = mt5.symbol_info_tick(order.get("symbol", "XAUUSD"))
        price = tick.ask if order["action"] == "BUY" else tick.bid
    if "sl" not in order or "tp" not in order:
        raise ValueError("Missing SL/TP")
    req = {
        "action": act,
        "symbol": order.get("symbol", "XAUUSD"),
        "volume": float(order["volume"]),
        "type": kind,
        "price": float(price),
        "sl": float(order["sl"]),
        "tp": float(order["tp"]),
        "deviation": 20,
        "magic": MAGIC,
        "comment": order.get("comment", "execution_operator"),
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN if act == mt5.TRADE_ACTION_PENDING else mt5.ORDER_FILLING_IOC,
    }
    res = mt5.order_send(req)
    if not res or res.retcode != mt5.TRADE_RETCODE_DONE:
        if act == mt5.TRADE_ACTION_PENDING and res and res.retcode in (10015, 10030):
            for fb in (mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK):
                req["type_filling"] = fb
                res = mt5.order_send(req)
                if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                    return res
        raise RuntimeError(f"order_failed retcode={getattr(res,'retcode',None)} comment={getattr(res,'comment',None)} last={mt5.last_error()}")
    return res


def process_signals(state):
    paths = sorted(SIGNAL_DIR.glob("*.json"))
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            log(f"bad_signal {path.name} {e}")
            continue
        if data.get("status") == "executed":
            continue
        required = ["action", "symbol", "volume", "sl", "tp"]
        if not all(k in data for k in required):
            log(f"missing_fields {path.name}")
            continue
        try:
            if not mt5.initialize(path=r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075"):
                log("mt5_init_failed")
                return state
            res = place_direct(data)
            out = {
                "status": "executed",
                "order": res._asdict() if hasattr(res, "_asdict") else res.__dict__,
            }
            path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
            log(f"executed {path.name} ticket={res.order if hasattr(res,'order') else 'n/a'}")
        except Exception as e:
            log(f"execution_failed {path.name} {e}")
        finally:
            mt5.shutdown()
    return state


def main():
    if not mt5.initialize(path=r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075"):
        log("initialize_failed")
        print(json.dumps({"status": "error", "reason": "initialize_failed"}))
        return
    state = load_state()
    if state.get("date") != d_date() or state.get("day_start_equity") is None:
        state = {"date": d_date(), "day_start_equity": equity(), "halted": False}
        save_state(state)
        log(f"day_start_equity={state['day_start_equity']}")
    equity_now = equity()
    drawdown = equity_now - state.get("day_start_equity", equity_now)
    if drawdown < MAX_DAILY_DRAWDOWN_USD:
        state["halted"] = True
        save_state(state)
        log(f"HALTED drawdown={drawdown}")
        print(json.dumps({"status": "halted", "drawdown_usd": drawdown}))
        mt5.shutdown()
        return
    state = process_signals(state)
    save_state(state)
    print(json.dumps({"status": "ok", "drawdown_usd": drawdown, "halted": state.get("halted", False)}))
    mt5.shutdown()


if __name__ == "__main__":
    import datetime as d
    main()
