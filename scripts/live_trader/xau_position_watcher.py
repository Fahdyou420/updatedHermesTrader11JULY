#!/usr/bin/env python3
"""
XAUUSD 1-Minute Position Watcher
- Direct MT5 API: initialize/shutdown each run
- Moves SL to breakeven + 1 point when profit >= 1R
- HALTS management if daily drawdown <= -2000 USD from day-start equity
- Logs every check; outputs JSON summary to stdout

Cron example (every minute):
* * * * * python "C:/Users/user/Desktop/hermes_claude/scripts/live_trader/xau_position_watcher.py"
"""

import json
import sys
import datetime
import logging
from pathlib import Path

try:
    import MetaTrader5 as mt5
except ImportError:
    print(json.dumps({
        "status": "error",
        "timestamp": datetime.datetime.now().isoformat(),
        "error": "MetaTrader5 package not installed. Install with: pip install MetaTrader5",
        "positions_checked": 0,
        "actions": [],
        "drawdown_usd": 0.0,
        "halted": False
    }))
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SYMBOL = "XAUUSD"
R_MULTIPLIER = 1.0              # Trigger SL move when profit >= 1R
BREAKEVEN_OFFSET_POINTS = 1     # +1 point above entry for longs, -1 for shorts
MAX_DAILY_DRAWDOWN_USD = -2000.0

# Runtime artifacts (created automatically by the script, not manual)
STATE_FILE = Path(__file__).with_suffix(".state.json")
LOG_FILE = Path(__file__).with_suffix(".log")

# ---------------------------------------------------------------------------
# Logging: logs go to stderr so stdout remains clean JSON
# ---------------------------------------------------------------------------
logger = logging.getLogger("xau_position_watcher")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File handler
if not logger.handlers:
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


# ---------------------------------------------------------------------------
# State helpers (auto-created runtime file)
# ---------------------------------------------------------------------------
def _load_state():
    today = str(datetime.date.today())
    default = {"date": today, "day_start_equity": None}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            if state.get("date") != today:
                return default
            return state
        except (json.JSONDecodeError, IOError):
            return default
    return default


def _save_state(state):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except IOError as e:
        logger.warning(f"Cannot write state file {STATE_FILE}: {e}")


def get_day_start_equity():
    """Return equity at start of trading day, initializing state if needed."""
    state = _load_state()
    today = str(datetime.date.today())

    if state.get("date") != today or state.get("day_start_equity") is None:
        account = mt5.account_info()
        if account is None:
            err = mt5.last_error()
            logger.error(f"account_info failed during day-start init: {err}")
            return None
        equity = float(account.equity)
        state = {"date": today, "day_start_equity": equity}
        _save_state(state)
        logger.info(f"New trading day detected. Day-start equity recorded: {equity:.2f} USD")
    return state.get("day_start_equity")


# ---------------------------------------------------------------------------
# Trading math
# ---------------------------------------------------------------------------
def get_symbol_meta():
    """Return (point, contract_size) for SYMBOL with safe fallbacks."""
    info = mt5.symbol_info(SYMBOL)
    if info is None:
        logger.warning(f"symbol_info({SYMBOL}) returned None; using fallback values")
        return 0.01, 100.0
    point = info.point if info.point and info.point > 0 else 0.01
    contract_size = getattr(info, "trade_contract_size", 100.0)
    if not contract_size or contract_size <= 0:
        contract_size = 100.0
    return point, contract_size


def calculate_r_dollars(position, point, contract_size):
    """
    Calculate initial risk in USD (1R).
    R = |entry - initial_SL| * contract_size * volume
    """
    sl = position.sl
    if sl is None or sl <= 0:
        return None

    entry = position.price_open
    if position.type == mt5.POSITION_TYPE_BUY:
        risk_price = entry - sl
    else:
        risk_price = sl - entry

    if risk_price <= 0:
        return None

    return risk_price * contract_size * position.volume


def compute_new_sl(position, point):
    """
    New SL = breakeven + offset_points in the profit direction.
    Returns None if the new SL would not improve the existing SL.
    """
    entry = position.price_open
    offset = BREAKEVEN_OFFSET_POINTS * point

    if position.type == mt5.POSITION_TYPE_BUY:
        new_sl = entry + offset
        if new_sl <= position.sl:
            return None  # Already at or beyond breakeven+1
        return new_sl
    else:
        new_sl = entry - offset
        if new_sl >= position.sl:
            return None
        return new_sl


def modify_position_sl(ticket, new_sl, tp):
    """Send order to modify SL while preserving TP."""
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": int(ticket),
        "sl": float(new_sl),
        "tp": float(tp) if tp and tp > 0 else 0.0,
    }
    result = mt5.order_send(request)
    if result is None:
        return False, "order_send returned None"
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return False, f"retcode={result.retcode} comment={result.comment}"
    return True, None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    run_timestamp = datetime.datetime.now().isoformat()
    actions = []
    positions_checked = 0
    halted = False
    status = "ok"
    drawdown_usd = 0.0
    last_global_error = None

    # Initialize MT5
    if not mt5.initialize(path=r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075"):
        err = mt5.last_error()
        logger.critical(f"MT5 initialization failed: {err}")
        print(json.dumps({
            "status": "error",
            "timestamp": run_timestamp,
            "positions_checked": 0,
            "actions": [],
            "drawdown_usd": 0.0,
            "halted": False,
            "error": f"MT5 init failed: {err}"
        }))
        sys.exit(1)

    try:
        # ---------------------------------------------------------------
        # 1) Daily equity / halt check
        # ---------------------------------------------------------------
        day_start_equity = get_day_start_equity()
        account = mt5.account_info()
        if account is None:
            raise RuntimeError(f"account_info() failed: {mt5.last_error()}")

        current_equity = float(account.equity)
        if day_start_equity is not None:
            drawdown_usd = current_equity - day_start_equity
            if drawdown_usd <= MAX_DAILY_DRAWDOWN_USD:
                halted = True
                status = "halted"
                logger.critical(
                    f"HALT | Daily drawdown {drawdown_usd:.2f} USD exceeds "
                    f"{MAX_DAILY_DRAWDOWN_USD} (day-start: {day_start_equity:.2f}, "
                    f"current equity: {current_equity:.2f})"
                )

        # ---------------------------------------------------------------
        # 2) Fetch positions and latest tick
        # ---------------------------------------------------------------
        positions = mt5.positions_get(symbol=SYMBOL)
        if positions is None:
            positions = []

        tick = mt5.symbol_info_tick(SYMBOL)
        point, contract_size = get_symbol_meta()

        logger.info(
            f"Check | Status={status} | Positions={len(positions)} | "
            f"Drawdown={drawdown_usd:.2f} USD | Halted={halted}"
        )

        # ---------------------------------------------------------------
        # 3) Iterate positions
        # ---------------------------------------------------------------
        for pos in positions:
            positions_checked += 1
            action_taken = "none"

            direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
            entry = float(pos.price_open)
            sl = float(pos.sl) if pos.sl else 0.0
            tp = float(pos.tp) if pos.tp else 0.0
            pnl = float(pos.profit)
            current_price = float(pos.price_current)

            # Prefer live tick for current price
            if tick:
                if pos.type == mt5.POSITION_TYPE_BUY:
                    current_price = float(tick.bid)
                else:
                    current_price = float(tick.ask)

            # R calculation
            r_dollars = calculate_r_dollars(pos, point, contract_size)
            profit_in_r = 0.0
            if r_dollars and r_dollars > 0:
                profit_in_r = pnl / r_dollars

            log_prefix = (
                f"Ticket={pos.ticket} Dir={direction} Entry={entry:.2f} "
                f"Price={current_price:.2f} SL={sl:.2f} TP={tp:.2f} "
                f"PnL={pnl:.2f} USD"
            )
            logger.info(f"{log_prefix} R={r_dollars if r_dollars else 0:.2f} ProfitR={profit_in_r:.2f}")

            action_error = None

            if r_dollars is None or r_dollars <= 0:
                action_taken = "none"
                logger.warning(f"{log_prefix} | ACTION=none | Reason=missing_or_invalid_SL")
            elif not halted and profit_in_r >= R_MULTIPLIER:
                new_sl = compute_new_sl(pos, point)
                if new_sl is not None:
                    success, err = modify_position_sl(pos.ticket, new_sl, pos.tp)
                    if success:
                        action_taken = f"moved_sl_to_{new_sl:.2f}"
                        logger.info(f"{log_prefix} | ACTION={action_taken}")
                    else:
                        action_taken = "sl_modify_failed"
                        action_error = err
                        logger.error(f"{log_prefix} | ACTION={action_taken} | Error={err}")
                        last_global_error = err
                else:
                    action_taken = "already_at_breakeven_plus"
                    logger.info(f"{log_prefix} | ACTION={action_taken}")
            elif halted:
                action_taken = "halted_no_action"
                logger.info(f"{log_prefix} | ACTION={action_taken}")
            else:
                # Profit in R is below threshold, no action
                logger.debug(f"{log_prefix} | ACTION=none | ProfitR={profit_in_r:.2f} < {R_MULTIPLIER}")

            actions.append({
                "ticket": int(pos.ticket),
                "direction": direction,
                "entry": round(entry, 2),
                "current_price": round(current_price, 2),
                "sl": round(sl, 2),
                "tp": round(tp, 2),
                "pnl_usd": round(pnl, 2),
                "r_dollars": round(r_dollars, 2) if r_dollars else None,
                "profit_in_r": round(profit_in_r, 4),
                "action": action_taken,
                "last_error": action_error
            })

    except Exception as e:
        last_global_error = str(e)
        logger.error(f"Unhandled exception in watcher: {e}", exc_info=True)
        status = "error"
    finally:
        mt5.shutdown()

    summary = {
        "status": status,
        "timestamp": run_timestamp,
        "positions_checked": positions_checked,
        "actions": actions,
        "drawdown_usd": round(drawdown_usd, 2),
        "halted": halted
    }

    print(json.dumps(summary, indent=2))

    if status == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
