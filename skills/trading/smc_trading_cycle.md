---
name: smc_trading_cycle
description: "Smart Money Concepts / ICT trading cycle for Hermes: bias, structure, FVG, order blocks, killzones, liquidity sweeps, and confluence filters."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, smc, ict, bias, fvg, ob]
---

# smc_trading_cycle

Use this skill when the user asks for HTF bias, SMC structure, FVG/OB detection, killzone filtering, liquidity sweeps, or confluence evaluation.

## Rules

- Establish bias on D1/H4 before M15 entries.
- Reject and log setups that contradict HTF bias.
- Use native MT5 service paths for live data when available.
- Require explicit entry trigger + confirmation + invalidation before any trade is considered valid.
