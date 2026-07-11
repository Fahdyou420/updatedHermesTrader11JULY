"""
Feed Integrity Guard — validates latest bars before they enter any signal or execution path.
If feed is stale/sparse/malformed, pauses entries and alerts via Redis.
"""
from __future__ import annotations

import os
import time
import json
import requests
from typing import Any, Dict, List, Optional

from services.shared.logger import get_logger

try:
    from services.shared import redis_channels
    from services.shared.error_bus import publish_error
except Exception:  # pragma: no cover
    redis_channels = None
    publish_error = None

logger = get_logger("feed_guard")

DEFAULT_BRIDGE_URL = os.getenv("MT5_BRIDGE_URL", "http://localhost:5558")
DEFAULT_NATIVE_URL = os.getenv("NATIVE_MT5_URL", "http://localhost:7779")
_STALE_AFTER_SECONDS = int(os.getenv("FEED_STALE_SECONDS", "180"))
_MIN_VOLUME = int(os.getenv("FEED_MIN_VOLUME", "1"))
_MAX_SPREAD_POINTS = int(os.getenv("FEED_MAX_SPREAD_POINTS", "500"))


class FeedGuard:
    def __init__(self) -> None:
        self.paused_until: float = 0.0
        self.last_ok_ts: float = 0.0
        self.reason: Optional[str] = None

    def _probe(self, instrument: str, timeframe: str = "M15") -> Optional[Dict[str, Any]]:
        for base in (DEFAULT_BRIDGE_URL, DEFAULT_NATIVE_URL):
            try:
                r = requests.get(
                    f"{base}/latest_bars?instrument={instrument}&tf={timeframe}&n=1",
                    timeout=3,
                )
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list) and data:
                        return data[-1]
            except Exception:
                continue
        return None

    def check(self, instrument: str = "XAUUSD", timeframe: str = "M15") -> bool:
        if time.time() < self.paused_until:
            return False

        bar = self._probe(instrument, timeframe)
        if bar is None:
            self.paused_until = time.time() + 60
            self.reason = "no_bars"
            self._alert(instrument, "no_bars")
            return False

        try:
            ts = int(bar.get("time", bar.get("timestamp", 0)))
        except Exception:
            ts = 0

        volume = int(bar.get("tick_volume", bar.get("volume", 0)))
        spread_pts = int(bar.get("spread", 0))

        if ts <= 0 or (time.time() - ts) > _STALE_AFTER_SECONDS:
            self.paused_until = time.time() + 60
            self.reason = "stale_bars"
            self._alert(instrument, "stale_bars", ts=ts)
            return False

        if volume < _MIN_VOLUME:
            self.paused_until = time.time() + 60
            self.reason = "zero_volume"
            self._alert(instrument, "zero_volume", volume=volume)
            return False

        if spread_pts > _MAX_SPREAD_POINTS:
            self.paused_until = time.time() + 30
            self.reason = "spread_breach"
            self._alert(instrument, "spread_breach", spread_pts=spread_pts)
            return False

        self.last_ok_ts = time.time()
        self.reason = None
        return True

    def _alert(self, instrument: str, reason: str, **kwargs: Any) -> None:
        msg = f"FEED_GUARD {instrument} paused: {reason} kwargs={kwargs}"
        logger.warning(msg)
        if publish_error:
            try:
                publish_error("feed_guard", "WARNING", msg, json.dumps(kwargs))
            except Exception:
                pass
        if redis_channels:
            try:
                import redis
                r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True)
                r.publish(redis_channels.PAPER_TRADE_UPDATE, json.dumps({
                    "type": "feed_guard_alert",
                    "instrument": instrument,
                    "reason": reason,
                    "kwargs": kwargs,
                }))
            except Exception:
                pass


feed_guard = FeedGuard()
