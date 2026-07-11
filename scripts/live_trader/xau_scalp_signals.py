import json, sys
from pathlib import Path
import MetaTrader5 as mt5

SYMBOL = "XAUUSD"
LOG = Path.home() / "HermesLogs" / "xau_scalp_signals.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

INDICATOR_PARAMS = {
    "fast_ma_period": 20,
    "slow_ma_period": 50,
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2.0,
    "adx_period": 14,
    "atr_period": 14,
    "timeframe": mt5.TIMEFRAME_M1,
    "bars": 200,
}


def log(msg: str):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.open("a", encoding="utf-8").write(f"{msg}\n")


def handle_mt5_error(source: str):
    err = mt5.last_error()
    log(f"{source} mt5_error={err}")
    return {"signal": "NONE", "confidence": 0.0, "reason": f"mt5_error_{err}"}


def main():
    if not mt5.initialize(path=r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075"):
        log("initialize_failed")
        print(json.dumps({"signal": "NONE", "confidence": 0.0, "reason": "initialize_failed"}))
        return

    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        out = handle_mt5_error("symbol_info")
        print(json.dumps(out))
        mt5.shutdown()
        return

    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        out = handle_mt5_error("symbol_info_tick")
        print(json.dumps(out))
        mt5.shutdown()
        return

    bars = mt5.copy_rates_from_pos(SYMBOL, INDICATOR_PARAMS["timeframe"], 0, INDICATOR_PARAMS["bars"])
    if bars is None or len(bars) < INDICATOR_PARAMS["slow_ma_period"] + 2:
        out = handle_mt5_error("copy_rates_from_pos")
        print(json.dumps(out))
        mt5.shutdown()
        return

    close = [bar["close"] for bar in bars]
    high = [bar["high"] for bar in bars]
    low = [bar["low"] for bar in bars]

    def ma(period: int):
        result = []
        for i in range(len(close)):
            if i < period - 1:
                result.append(0.0)
                continue
            result.append(sum(close[i - period + 1 : i + 1]) / period)
        return result

    fast_ma = ma(INDICATOR_PARAMS["fast_ma_period"])
    slow_ma = ma(INDICATOR_PARAMS["slow_ma_period"])

    def rsi(period: int):
        gains, losses = [], []
        for i in range(1, len(close)):
            change = close[i] - close[i - 1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        result = [0.0] * period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(100 - (100 / (1 + rs)))
        return result

    rsi_values = rsi(INDICATOR_PARAMS["rsi_period"])

    def macd(fast: int, slow: int, signal: int):
        fast_ma_vals = ma(fast)
        slow_ma_vals = ma(slow)
        macd_line = [fast_ma_vals[i] - slow_ma_vals[i] for i in range(len(close))]
        signal_line = ma(signal)
        signal_ma = [sum(macd_line[i - signal + 1 : i + 1]) / signal for i in range(len(macd_line))]
        histogram = [macd_line[i] - signal_ma[i] for i in range(len(macd_line))]
        return macd_line, signal_ma, histogram

    _, _, histogram = macd(
        INDICATOR_PARAMS["macd_fast"],
        INDICATOR_PARAMS["macd_slow"],
        INDICATOR_PARAMS["macd_signal"],
    )

    def bollinger(period: int, std_dev: float):
        mid, upper, lower = [], [], []
        for i in range(len(close)):
            if i < period - 1:
                mid.append(0.0)
                upper.append(0.0)
                lower.append(0.0)
                continue
            window = close[i - period + 1 : i + 1]
            avg = sum(window) / period
            variance = sum((price - avg) ** 2 for price in window) / period
            std = variance**0.5
            mid.append(avg)
            upper.append(avg + std_dev * std)
            lower.append(avg - std_dev * std)
        return mid, upper, lower

    bb_mid, bb_upper, bb_lower = bollinger(INDICATOR_PARAMS["bb_period"], INDICATOR_PARAMS["bb_std"])

    def adx(period: int):
        plus_dm, minus_dm = [], []
        for i in range(1, len(high)):
            up = high[i] - high[i - 1]
            down = low[i - 1] - low[i]
            plus_dm.append(max(up, 0) if up > down else 0)
            minus_dm.append(max(down, 0) if down > up else 0)
        atr_vals = atr(period)
        smoothed_plus = sum(plus_dm[:period])
        smoothed_minus = sum(minus_dm[:period])
        dx_vals = []
        for i in range(period, len(plus_dm)):
            smoothed_plus = smoothed_plus - (smoothed_plus / period) + plus_dm[i]
            smoothed_minus = smoothed_minus - (smoothed_minus / period) + minus_dm[i]
            tr = atr_vals[i] if i < len(atr_vals) else 0
            if tr == 0:
                dx_vals.append(0.0)
                continue
            plus_di = 100 * (smoothed_plus / tr)
            minus_di = 100 * (smoothed_minus / tr)
            di_sum = plus_di + minus_di
            dx_vals.append(0.0 if di_sum == 0 else 100 * abs(plus_di - minus_di) / di_sum)
        smoothed_dx = [0.0] * period
        for i in range(period, len(dx_vals)):
            smoothed_dx.append(sum(dx_vals[i - period + 1 : i + 1]) / period)
        return smoothed_dx

    def atr(period: int):
        tr_vals = []
        for i in range(1, len(high)):
            tr = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
            tr_vals.append(tr)
        atr_vals = []
        for i in range(len(tr_vals)):
            if i < period - 1:
                atr_vals.append(0.0)
                continue
            atr_vals.append(sum(tr_vals[i - period + 1 : i + 1]) / period)
        return atr_vals

    adx_values = adx(INDICATOR_PARAMS["adx_period"])
    atr_values = atr(INDICATOR_PARAMS["atr_period"])
    price = tick.ask if tick.ask > 0 else tick.bid
    digits = getattr(symbol_info, "digits", 2)
    point = getattr(symbol_info, "point", 0.01)

    def round_price(value: float) -> float:
        return round(value, digits)

    current_fast = fast_ma[-1]
    current_slow = slow_ma[-1]
    prev_fast = fast_ma[-2]
    prev_slow = slow_ma[-2]
    current_rsi = rsi_values[-1] if rsi_values else 50.0
    current_hist = histogram[-1]
    prev_hist = histogram[-2]
    current_bb_width = bb_upper[-1] - bb_lower[-1]
    bb_touch_long = current_bb_width > 0 and abs(price - bb_lower[-1]) / current_bb_width < 0.25
    bb_touch_short = current_bb_width > 0 and abs(price - bb_upper[-1]) / current_bb_width < 0.25
    adx_value = adx_values[-1] if adx_values else 0.0
    atr_value = atr_values[-1] if atr_values else 0.0

    if atr_value <= 0:
        out = {"signal": "NONE", "confidence": 0.0, "reason": "invalid_atr"}
        print(json.dumps(out))
        mt5.shutdown()
        return

    confidence = 0.0
    reasons = []
    if current_fast > current_slow and prev_fast <= prev_slow:
        reasons.append("fast_ma_crossed_above")
    if 40 <= current_rsi <= 60:
        reasons.append("rsi_neutral")
    if current_hist > prev_hist and current_hist > 0:
        reasons.append("macd_rising")
    if bb_touch_long:
        reasons.append("bb_lower_touch")
    if adx_value > 20:
        reasons.append("adx_strong")
    if reasons:
        confidence = min(len(reasons) * 0.2, 1.0)

    if confidence >= 0.6 and current_fast > current_slow:
        sl = round_price(price - 1.2 * atr_value)
        tp = round_price(price + 1.4 * atr_value)
        out = {
            "signal": "BUY",
            "entry": round_price(price),
            "sl": sl,
            "tp": tp,
            "confidence": round(confidence, 2),
            "reason": " | ".join(reasons),
        }
        log(f"long {out}")
        print(json.dumps(out))
        mt5.shutdown()
        return

    confidence = 0.0
    reasons = []
    if current_fast < current_slow and prev_fast >= prev_slow:
        reasons.append("fast_ma_crossed_below")
    if 40 <= current_rsi <= 60:
        reasons.append("rsi_neutral")
    if current_hist < prev_hist and current_hist < 0:
        reasons.append("macd_falling")
    if bb_touch_short:
        reasons.append("bb_upper_touch")
    if adx_value > 20:
        reasons.append("adx_strong")
    if reasons:
        confidence = min(len(reasons) * 0.2, 1.0)

    if confidence >= 0.6 and current_fast < current_slow:
        sl = round_price(price + 1.2 * atr_value)
        tp = round_price(price - 1.4 * atr_value)
        out = {
            "signal": "SELL",
            "entry": round_price(price),
            "sl": sl,
            "tp": tp,
            "confidence": round(confidence, 2),
            "reason": " | ".join(reasons),
        }
        log(f"short {out}")
        print(json.dumps(out))
        mt5.shutdown()
        return

    out = {"signal": "NONE", "confidence": 0.0, "reason": "no_signal"}
    print(json.dumps(out))
    mt5.shutdown()


if __name__ == "__main__":
    main()
