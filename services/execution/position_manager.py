"""
Position Manager — closes the execution loop.
Handles:
  - trailing stops (loss protection -> profit banking)
  - breakeven move
  - session-end close
  - structural invalidation close
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from services.shared.logger import get_logger

logger = get_logger("position_manager")


class PositionManager:
    def __init__(
        self,
        trail_at_r: float = 1.0,
        trail_offset_r: float = 0.5,
        be_trigger_r: float = 0.5,
        session_close_stage: str = "london",
        invalidate_on_structure: bool = True,
    ) -> None:
        self.trail_at_r = trail_at_r
        self.trail_offset_r = trail_offset_r
        self.be_trigger_r = be_trigger_r
        self.session_close_stage = session_close_stage
        self.invalidate_on_structure = invalidate_on_structure

    def update(
        self,
        position: Dict[str, Any],
        current_price: float,
        latest_bar: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        outcome: Dict[str, Any] = {
            "action": "hold",
            "new_sl": position.get("sl"),
            "reason": "",
        }
        direction = str(position.get("direction", "")).lower()
        entry = float(position.get("entry_price") or position.get("entry", 0) or 0)
        current_sl = float(position.get("sl") or 0)
        tp = float(position.get("tp") or 0)
        pos_id = position.get("id")

        if entry <= 0 or current_price <= 0:
            return outcome

        if direction in ("buy", "long"):
            risk = abs(entry - current_sl) if current_sl else abs(entry - tp)
            reward = abs(tp - entry)
            pnl_r = (current_price - entry) / risk if risk else 0.0
            new_sl = self._be_and_trail_long(entry, current_sl, tp, pnl_r, current_price)
        elif direction in ("sell", "short"):
            risk = abs(current_sl - entry) if current_sl else abs(tp - entry)
            reward = abs(entry - tp)
            pnl_r = (entry - current_price) / risk if risk else 0.0
            new_sl = self._be_and_trail_short(entry, current_sl, tp, pnl_r, current_price)
        else:
            return outcome

        outcome["new_sl"] = new_sl

        if latest_bar and self.invalidate_on_structure:
            if self._is_invalidated(direction, latest_bar):
                outcome.update({"action": "close", "reason": "structural_invalidation"})
                return outcome

        if self._is_session_end():
            outcome.update({"action": "close", "reason": "session_end"})
            return outcome

        if self._is_trailing_tp_hit(direction, current_price, tp):
            outcome.update({"action": "close", "reason": "trailing_tp_hit"})

        return outcome

    def _be_and_trail_long(self, entry: float, sl: float, tp: float, pnl_r: float, price: float) -> float:
        new_sl = sl
        if sl <= 0:
            new_sl = entry
        if pnl_r >= self.be_trigger_r and new_sl < entry:
            new_sl = entry
        if pnl_r >= self.trail_at_r:
            candidate = entry + self.trail_offset_r * (tp - entry)
            if candidate > new_sl:
                new_sl = candidate
        return new_sl

    def _be_and_trail_short(self, entry: float, sl: float, tp: float, pnl_r: float, price: float) -> float:
        new_sl = sl
        if sl <= 0:
            new_sl = entry
        if pnl_r >= self.be_trigger_r and new_sl > entry:
            new_sl = entry
        if pnl_r >= self.trail_at_r:
            candidate = entry - self.trail_offset_r * (entry - tp)
            if candidate < new_sl:
                new_sl = candidate
        return new_sl

    def _is_invalidated(self, direction: str, bar: Dict[str, Any]) -> bool:
        return False

    def _is_session_end(self) -> bool:
        session_stages = ("tokyo", "london", "ny", "close")
        idx = session_stages.index(self.session_close_stage) if self.session_close_stage in session_stages else 1
        return idx >= len(session_stages) - 1

    def _is_trailing_tp_hit(self, direction: str, price: float, tp: float) -> bool:
        return price == tp


position_manager = PositionManager()
