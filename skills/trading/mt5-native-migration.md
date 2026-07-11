---
name: mt5-native-migration
description: "Replace legacy EA/MQL5/ZMQ bridge architecture with the native MetaTrader5 Python package on the Windows host. Scaffold, parallel-validate, parity-test, cutover, and auto-reconnect monitoring."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, mt5, native, migration, parity, windows, host-service]
---

# MT5-Native Migration Department

Use this skill whenever the user asks to migrate MT5 integration to native Python, validate native parity with ZMQ bridge, or manage host-level MT5 service scaffolding.

## Hard Constraint

The `MetaTrader5` Python package only works on the same machine as a logged-in MT5 terminal via local IPC. This service must run on the Windows host, not inside Docker.

## Task Stages

- TASK A native-service-scaffold: host-level Python service exposing latest_bars, account_state, positions, trade_history, order execution with JSON response shapes matching mt5_bridge.
- TASK B parallel-validation: run alongside ZMQ mt5_bridge; pull all data types from both simultaneously and diff results. Any mismatch blocks progression.
- TASK C order-execution-parity-test: paper-mode identical order through both paths if possible, otherwise through native alone with manual observation.
- TASK D cutover: only after clean parity for at least 24 hours of real market time.
- TASK E reliability-check: cron ensures mt5.initialize(path=r"C:\Program Files\MetaTrader 5	erminal64.exe") connection health and auto-reconnect; logs every reconnect event.

## Cutover Rules

- Old EA/ZMQ code remains in repo but is marked deprecated; do not delete during transition.
- Rollback safety net must remain available for at least one week after cutover.

## Data Policy

All live data reads use the native MT5 service path. Historical local data remains under `data/market_data/`.
