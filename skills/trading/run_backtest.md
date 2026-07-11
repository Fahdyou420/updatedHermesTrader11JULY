---
name: run_backtest
description: "Run backtests for Hermes trading strategies against local market data or the Docker backtester. Use whenever the user asks to backtest, validate a strategy, or produce trade journals."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, backtest, validation, journal]
---

# run_backtest

Use this skill whenever the user asks to run a backtest, validate a strategy, or produce trade journals.

## Behavior

- Prefer the journaled local backtest path with explicit per-trade timestamps and #Test_OPS.
- Never fabricate results. Empty/0-trade runs must be recorded as inconclusive or rejected with exact metrics.
- For service-backed backtests, log `docker logs hermes_backtester --since/--until` timestamps alongside the result.
- Apply hard gates when requested: win_rate>=0.52, expectancy>=0.40R, max_drawdown<=10%, trades>=50.
- Write artifacts under `data/rnd/results/` and update strategy cards in `02_STRATEGIES/active/` only with verified outputs.
