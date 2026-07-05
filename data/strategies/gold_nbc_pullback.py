"""
Gold NBC Pullback — Daily bars
Inherits BaseStrategy.
"""
import math
from services.backtester.strategies.base import BaseStrategy
from services.shared.models import StrategyConfig

class GoldNBCTrendPullback(BaseStrategy):
    @staticmethod
    def name() -> str:
        return "gold_nbc_pullback"

    def find_signal(self, bars, i, smc=None, triggered_ids=None):
        if i < 60 or i >= len(bars):
            return None
        closes = [float(b.get("close", 0)) for b in bars[max(0, i-120):i+1]]
        highs = [float(b.get("high", 0)) for b in bars[max(0, i-120):i+1]]
        lows = [float(b.get("low", 0)) for b in bars[max(0, i-120):i+1]]
        if len(closes) < 20:
            return None

        cur_close = closes[-1]
        ema20 = sum(closes[-20:]) / 20.0
        sma20 = sum(closes[-20:]) / 20.0
        sma_w = sum(closes[-60:]) / 60.0  # weekly-like proxy when only ~120 bars provided
        deltas = [closes[j] - closes[j-1] for j in range(1, len(closes))]
        gains = [d for d in deltas[-14:] if d > 0]
        losses = [-d for d in deltas[-14:] if d < 0]
        avg_gain = sum(gains)/14.0 if gains else 0.0
        avg_loss = sum(losses)/14.0 if losses else 0.0
        rsi = 100 - 100/(1 + avg_gain/avg_loss) if avg_loss else 50.0

        trs = [max(highs[j]-lows[j], abs(highs[j]-closes[j-1]), abs(lows[j]-closes[j-1])) for j in range(1, len(highs))]
        atr = sum(trs[-14:])/14.0 if len(trs) >= 14 else 0.0
        if atr <= 0:
            return None
        if sma20 < sma_w:
            return None
        if not (rsi < 40 and cur_close <= ema20):
            return None
        sl = cur_close - 1.5 * atr
        tp = cur_close + 2.5 * atr
        if sl >= tp or sl <= 0:
            return None
        return {
            "direction": "long",
            "entry_price": cur_close,
            "sl": sl,
            "tp": tp,
            "lots": 0.1,
            "timeframe": "D1",
            "strategy_id": self.__class__.name(),
            "setup_type": "nbc_pullback",
            "confidence": "medium",
            "agent_notes": "weekly trend + daily pullback with ATR SL/TP"
        }
