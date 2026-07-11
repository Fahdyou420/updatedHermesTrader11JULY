"""
Bridge Watchdog — monitors MT5 bridge + native endpoints, publishes health to Redis, and can restart the bridge service.
"""
from __future__ import annotations

import os
import time
import json
import subprocess
import threading
from typing import Any, Dict, Optional

from services.shared.logger import get_logger

logger = get_logger("bridge_watchdog")

MT5_BRIDGE_URL = os.getenv("MT5_BRIDGE_URL", "http://localhost:5558")
NATIVE_MT5_URL = os.getenv("NATIVE_MT5_URL", "http://localhost:7779")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
HEALTH_KEY = "hermes:bridge:health"
BRIDGE_FAIL_THRESHOLD = 15  # consider down after 15 consecutive failures
CHECK_INTERVAL = 15

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis as redis_mod
            _redis_client = redis_mod.from_url(REDIS_URL, decode_responses=True)
        except Exception:
            return None
    return _redis_client


class BridgeState:
    bridge_ok = False
    native_ok = False
    bridge_fails = 0
    native_fails = 0
    last_bridge_ok = 0.0
    last_native_ok = 0.0
    last_check = 0.0
    restarting = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bridge_ok": self.bridge_ok,
            "native_ok": self.native_ok,
            "bridge_fails": self.bridge_fails,
            "native_fails": self.native_fails,
            "last_bridge_ok": self.last_bridge_ok,
            "last_native_ok": self.last_native_ok,
            "last_check": self.last_check,
            "restarting": self.restarting,
        }


def _http_get(url: str, timeout: int = 2) -> tuple[bool, Optional[str]]:
    import requests
    try:
        r = requests.get(url, timeout=timeout)
        if 200 <= r.status_code < 300:
            return True, None
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


def _publish(state: BridgeState) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        r.setex(HEALTH_KEY, 30, json.dumps(state.to_dict()))
    except Exception:
        pass


def _restart_bridge() -> None:
    if BridgeState.restarting:
        return
    BridgeState.restarting = True
    logger.warning("Attempting to restart MT5 bridge service...")
    try:
        subprocess.run(
            ["docker", "compose", "up", "-d", "mt5_bridge"],
            check=False,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
    except Exception as e:
        logger.error("Bridge restart failed: %s", e)
    finally:
        time.sleep(10)
        BridgeState.restarting = False


def tick(state: BridgeState) -> None:
    state.last_check = time.time()
    state.bridge_ok, bridge_err = _http_get(f"{MT5_BRIDGE_URL}/health")
    state.native_ok, native_err = _http_get(f"{NATIVE_MT5_URL}/health")

    if state.bridge_ok:
        state.bridge_fails = 0
        state.last_bridge_ok = time.time()
    else:
        state.bridge_fails += 1
        if state.bridge_fails >= BRIDGE_FAIL_THRESHOLD:
            logger.critical("Bridge watchdog: bridge appears down (fails=%d, err=%s)", state.bridge_fails, bridge_err)
            _restart_bridge()

    if state.native_ok:
        state.native_fails = 0
        state.last_native_ok = time.time()
    else:
        state.native_fails += 1
        if state.native_fails >= BRIDGE_FAIL_THRESHOLD:
            logger.critical("Bridge watchdog: native MT5 API appears down (fails=%d, err=%s)", state.native_fails, native_err)

    _publish(state)


def watch_loop() -> None:
    state = BridgeState()
    while True:
        try:
            tick(state)
        except Exception as e:
            logger.error("Bridge watchdog loop error: %s", e)
        time.sleep(CHECK_INTERVAL)


def start_watchdog_thread() -> threading.Thread:
    t = threading.Thread(target=watch_loop, daemon=True)
    t.start()
    logger.info("Bridge watchdog started with %ds interval", CHECK_INTERVAL)
    return t
