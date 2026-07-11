from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5
import numpy as np
import pandas as pd

# ----------------------------
# Config / Risk constraints
# ----------------------------
INSTRUMENT = os.getenv("XAUUSD", "XAUUSD")
MAX_RISK_PCT = float(os.getenv("MAX_RISK_PCT", "0.005"))   # 0.5% per trade
MAX_DAILY_DD_USD = float(os.getenv("MAX_DAILY_DD_USD", "2000.0"))
RISK_PER_TRADE_USD = float(os.getenv("RISK_PER_TRADE_USD", "0.0"))  # override if provided
BASE_LOT = float(os.getenv("BASE_LOT", 0.01))
LOOKBACK_TRADING = 300
LOOKBACK_HTF = 500
LOG = Path(os.getenv("HERMES_LOG_DIR", Path.home() / "HermesLogs")) / "xau_scalper.log"
MTF_DIR = Path(os.getenv("HERMES_SKILLS_DIR", Path.home() / ".hermes" / "skills" / "trading"))
TRADE_JOURNAL = MTF_DIR / "03_TRADE_JOURNAL" if False else None


# ----------------------------
# MT5 helpers
# ----------------------------

def mt5_init():
    if not mt5.initialize(path=r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075"):
        raise SystemExit(f"MT5 init failed: {mt5.last_error()}")
    sym = mt5.symbol_info(INSTRUMENT)
    if not sym:
        raise SystemExit(f"Symbol {INSTRUMENT} unavailable: {mt5.last_error()}")
    return sym


def fetch_bars(tf: str, n: int) -> pd.DataFrame:
    timeframe = getattr(mt5, tf, None)
    if timeframe is None or tf not in {
        "TIMEFRAME_M1", "TIMEFRAME_M5", "TIMEFRAME_M15", "TIMEFRAME_H1", "TIMEFRAME_H4", "TIMEFRAME_D1"
    }:
        raise ValueError(f"Unsupported tf {tf}")
    raw = mt5.copy_rates_from_pos(INSTRUMENT, timeframe, 0, n)
    if raw is None or len(raw) == 0:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"])
    df = pd.DataFrame(raw)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


# ----------------------------
# Indicators
# ----------------------------

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def bollinger(series: pd.Series, length: int = 20, mult: float = 2.0):
    ma = series.rolling(length).mean()
    std = series.rolling(length).std(ddof=0)
    upper = ma + mult * std
    lower = ma - mult * std
    return ma, upper, lower


def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=length - 1, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(com=length - 1, adjust=False, min_periods=length).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    return 100 - 100 / (1 + rs)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14):
    h = high.astype(float)
    l = low.astype(float)
    c = close.astype(float)
    tr1 = h - l
    tr2 = (h - c.shift(1)).abs()
    tr3 = (l - c.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(com=length - 1, adjust=False, min_periods=length).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    fast_ma = ema(close, fast)
    slow_ma = ema(close, slow)
    macd_line = fast_ma - slow_ma
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    vwap = (tp * df["tick_volume"]).cumsum() / df["tick_volume"].cumsum()
    return vwap


def obv(close: pd.Series, tick_volume) -> pd.Series:
    direction = close.diff().clip(lower=0).fillna(0) - close.diff().clip(upper=0).fillna(0)
    obv = (direction * tick_volume).cumsum()
    return obv


# ----------------------------
# Account / risk helpers
# ----------------------------

def account_state():
    info = mt5.account_info()
    if not info:
        raise SystemExit(f"account_info failed: {mt5.last_error()}")
    return info._asdict()


def open_positions():
    pos = mt5.positions_get(symbol=INSTRUMENT)
    return [p._asdict() for p in (pos or [])]


def today_realized_loss() -> float:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    deals = mt5.history_deals_get(int(start.timestamp()), int(datetime.now(timezone.utc).timestamp()))
    if not deals:
        return 0.0
    total = 0.0
    for d in deals:
        if getattr(d, "symbol", None) == INSTRUMENT and getattr(d, "entry", None) in (0, 1) and getattr(d, "type", None) in (0, 1) and d.profit < 0:
            total += abs(float(d.profit))
    return total


def risk_lot(sl_distance: float) -> float:
    acct = account_state()
    balance = float(acct.get("balance", 0.0) or 0.0)
    risk_usd = RISK_PER_TRADE_USD if RISK_PER_TRADE_USD > 0 else min(balance * MAX_RISK_PCT, balance * 0.01)
    if sl_distance <= 0:
        return BASE_LOT
    lot = risk_usd / (sl_distance * float(mt5.symbol_info(INSTRUMENT).trade_contract_size))
    lot = max(BASE_LOT, float(np.floor(lot * 100.0)) / 100.0)
    return min(lot, 1.0)


def broker_compliant_sl_tp(direction: str, entry: float, sl: float, tp: float):
    sym = mt5.symbol_info(INSTRUMENT)
    tick = mt5.symbol_info_tick(INSTRUMENT)
    if sym is None or tick is None:
        return entry, sl, tp
    sl_dist = abs(entry - sl)
    tp_dist = abs(tp - entry)
    if sl_dist < sym.trade_stops_level * sym.point and sym.trade_stops_level:
        sl = entry - sym.trade_stops_level * sym.point if direction == "LONG" else entry + sym.trade_stops_level * sym.point
    if tp_dist < sym.trade_stops_level * sym.point and sym.trade_stops_level:
        tp = entry + sym.trade_stops_level * sym.point if direction == "LONG" else entry - sym.trade_stops_level * sym.point
    if direction == "LONG" and sl >= entry:
        sl = entry - sym.point
    if direction == "SHORT" and sl <= entry:
        sl = entry + sym.point
    if direction == "LONG" and tp <= entry:
        tp = entry + sym.point * 100
    if direction == "SHORT" and tp >= entry:
        tp = entry - sym.point * 100
    return round(float(entry), sym.digits), round(float(sl), sym.digits), round(float(tp), sym.digits)


def send_pending_limit(direction: str, price: float, sl: float, tp: float, volume: float, comment: str = "hermes_scalp"):
    sym = mt5.symbol_info(INSTRUMENT)
    entry, sl, tp = broker_compliant_sl_tp(direction, price, sl, tp)
    type_map = {"LONG": mt5.ORDER_TYPE_BUY_LIMIT, "SHORT": mt5.ORDER_TYPE_SELL_LIMIT}
    req = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": INSTRUMENT,
        "volume": float(volume),
        "price": float(entry),
        "type": type_map[direction],
        "sl": float(sl),
        "tp": float(tp),
        "deviation": 20,
        "magic": 123456,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    res = mt5.order_send(req)
    if not res or res.retcode != mt5.TRADE_RETCODE_DONE:
        raise SystemExit(f"Pending order failed: {getattr(res,'retcode',None)} {getattr(res,'comment',None)} {mt5.last_error()}")
    return res.order, entry, sl, tp


def send_market_if_validated(direction: str, price: float, sl: float, tp: float, volume: float, comment: str = "hermes_scalp"):
    sym = mt5.symbol_info(INSTRUMENT)
    tick = mt5.symbol_info_tick(INSTRUMENT)
    if tick is None:
        raise SystemExit("No tick")
    entry, sl, tp = broker_compliant_sl_tp(direction, price if price else (tick.ask if direction == "LONG" else tick.bid), sl, tp)
    type_map = {"LONG": mt5.ORDER_TYPE_BUY, "SHORT": mt5.ORDER_TYPE_SELL}
    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": INSTRUMENT,
        "volume": float(volume),
        "type": type_map[direction],
        "price": float(tick.ask if direction == "LONG" else tick.bid),
        "sl": float(sl),
        "tp": float(tp),
        "deviation": 20,
        "magic": 123456,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    res = mt5.order_send(req)
    if not res or res.retcode != mt5.TRADE_RETCODE_DONE:
        raise SystemExit(f"Market order failed: {getattr(res,'retcode',None)} {getattr(res,'comment',None)} {mt5.last_error()}")
    return res.order, entry, sl, tp


# ----------------------------
# Signal logic
# ----------------------------

def htf_context():
    d1 = fetch_bars("TIMEFRAME_D1", 60)
    h4 = fetch_bars("TIMEFRAME_H4", 80)
    bias = "NEUTRAL"
    if len(d1) > 20:
        d1_ema = ema(d1["close"], 20).iloc[-1]
        bias = "BULLISH" if d1["close"].iloc[-1] > d1_ema else "BEARISH"
    htf = {"bias": bias}
    return htf


def generate_signal(tf="TIMEFRAME_M5"):
    ctx = htf_context()
    df = fetch_bars(tf, 260)
    if df.empty or len(df) < 80:
        return None
    sym = mt5.symbol_info(INSTRUMENT)
    tick = mt5.symbol_info_tick(INSTRUMENT)
    point = sym.point
    digits = sym.digits

    df["fast"] = ema(df["close"], 10)
    df["slow"] = ema(df["close"], 50)
    df["rsi"] = rsi(df["close"], 14)
    df["macd_line"], df["signal_line"], df["hist"] = macd(df["close"], 12, 26, 9)
    df["atr"] = atr(df["high"], df["low"], df["close"], 14)
    df["boll_mid"], df["boll_upper"], df["boll_lower"] = bollinger(df["close"], 20, 2.0)
    df["vwap"] = vwap(df)
    df["obv"] = obv(df["close"], df["tick_volume"].fillna(0).astype(float))
    df["obv_slope"] = df["obv"].diff().rolling(8).mean()

    row = df.iloc[-1]
    prev = df.iloc[-2]
    price = round(float(tick.bid if ctx["bias"] != "BULLISH" else tick.ask), digits)
    atr_s = float(row["atr"]) if pd.notna(row["atr"]) else 0.0
    if atr_s == 0:
        return None

    long_cond = (
        row["fast"] > row["slow"] and prev["fast"] <= prev["slow"]
        and 40 < row["rsi"] < 68
        and row["hist"] > 0 and prev["hist"] <= 0
        and row["close"] <= row["boll_mid"] or False
        and row["obv_slope"] > 0
    )
    short_cond = (
        row["fast"] < row["slow"] and prev["fast"] >= prev["slow"]
        and 32 < row["rsi"] < 60
        and row["hist"] < 0 and prev["hist"] >= 0
        and row["obv_slope"] < 0
    )

    if long_cond:
        sl = price - 1.2 * atr_s
        tp = price + 1.8 * atr_s
        return {"instrument": INSTRUMENT, "direction": "LONG", "entry": price, "sl": sl, "tp": tp, "atr": atr_s, "bias": ctx["bias"], "reason": "ema_x+macd+rsi+obv"}

    if short_cond:
        sl = price + 1.2 * atr_s
        tp = price - 1.8 * atr_s
        return {"instrument": INSTRUMENT, "direction": "SHORT", "entry": price, "sl": sl, "tp": tp, "atr": atr_s, "bias": ctx["bias"], "reason": "ema_x+macd+rsi+obv"}
    return None


# ----------------------------
# Trade manager / watcher logic
# ----------------------------

def manage_open_positions():
    acct = account_state()
    realized = today_realized_loss()
    daily_limit = MAX_DAILY_DD_USD
    halted = realized >= daily_limit
    positions = open_positions()
    actions = []
    for p in positions:
        ticket = int(p["ticket"])
        ptype = p["type"]
        entry = float(p["price_open"])
        sl = float(p["sl"] or 0)
        tp = float(p["tp"] or 0)
        vol = float(p["volume"])
        current = float(p["price_current"])
        tick = mt5.symbol_info_tick(INSTRUMENT)
        price_for_sl = tick.bid if ptype == 0 else tick.ask
        if ptype == 0:
            r = (current - entry) / (entry - sl + 1e-9)
        else:
            r = (entry - current) / (sl - entry + 1e-9)
        if r is None or not np.isfinite(r):
            r = 0.0
        if 0.95 <= r <= 1.05 and sl != entry:
            move_sl = True
        else:
            move_sl = False
        if move_sl and not halted:
            req = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": INSTRUMENT,
                "position": ticket,
                "sl": float(entry),
                "tp": float(tp),
                "magic": 123456,
                "comment": "breakeven",
            }
            res = mt5.order_send(req)
            actions.append({"ticket": ticket, "action": "move_sl_to_be", "retcode": res.retcode, "msg": res.comment})
    return {"halted": halted, "realized_loss": realized, "limit": daily_limit, "open": len(positions), "actions": actions}


# ----------------------------
# Main entry
# ----------------------------

def run_watch():
    mt5_init()
    out = manage_open_positions()
    log_line = json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "status": "ok", **out}, default=str)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception:
        pass
    print(log_line)


def run_scalp():
    mt5_init()
    sym = mt5.symbol_info(INSTRUMENT)
    tick = mt5.symbol_info_tick(INSTRUMENT)
    spread = abs(float(tick.ask) - float(tick.bid))
    if spread > 50.0 * sym.point:
        print(json.dumps({"status": "reject", "reason": "spread_too_wide", "spread": spread}))
        return
    state = account_state()
    bal = float(state["balance"])
    realized = today_realized_loss()
    if realized >= MAX_DAILY_DD_USD:
        print(json.dumps({"status": "halted", "reason": "daily_dd_limit", "realized": realized, "limit": MAX_DAILY_DD_USD}))
        return
    if len(open_positions()) >= 3:
        print(json.dumps({"status": "full", "reason": "max_3_positions"}))
        return
    signal = generate_signal("TIMEFRAME_M1")
    if not signal:
        print(json.dumps({"status": "no_signal", "time": datetime.now(timezone.utc).isoformat()}))
        return
    dist = abs(signal["entry"] - signal["sl"])
    lots = risk_lot(dist)
    if lots < BASE_LOT:
        lots = BASE_LOT
    order_ticket, entry, sl, tp = send_pending_limit(signal["direction"], signal["entry"], signal["sl"], signal["tp"], lots, comment="hermes_scalp_1m")
    out = {
        "status": "pending_placed",
        "time": datetime.now(timezone.utc).isoformat(),
        "instrument": INSTRUMENT,
        "direction": signal["direction"],
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "lots": lots,
        "bias": signal["bias"],
        "reason": signal["reason"],
        "order": order_ticket,
        "atr": signal["atr"],
        "balance": bal,
        "daily_realized_loss": realized,
    }
    print(json.dumps(out, default=str))


if __name__ == "__main__":
    cmd = os.getenv("XAU_CMD", "scalp")
    if cmd == "watch":
        run_watch()
    else:
        run_scalp()
