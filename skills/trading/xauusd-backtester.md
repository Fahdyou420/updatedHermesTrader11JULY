---
name: xauusd-backtester
description: "XAUUSD-specific backtest procedures, datasets, and evidence rules for Hermes."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, xauusd, backtest, gold, evidence]
---

# xauusd-backtester

Use this skill whenever the user asks to backtest XAUUSD SMC strategies, review gold strategy evidence, or validate XAUUSD trade journals.

## Evidence Requirements

- Use local market data from `data/market_data/` unless explicitly instructed to hit live endpoints.
- Record exact trade journals with UTC timestamps.
- Do not promote a strategy from `hypothesis` to any passing status without explicit backtest approval.
- Treat `422` schema errors or missing datasets as primary evidence, not transient noise.
