---
id: gold_breakout
name: gold_breakout
strategy_id: gold_breakout
instrument: XAUUSD
timeframe: D1
status: hypothesis
source: custom
author: Hermes Agent
date_created: 2026-07-06
tags:
  - gold
  - breakout
  - daily
  - hypothesis
```

# gold_breakout
Daily/H4/M15 breakout strategy for XAUUSD.

## Logic
- Close above previous 20-bar high on daily
- Weekly EMA bias filter: only long when weekly bias is bullish
- ATR-based SL: below breakout high by 0.5 ATR
- ATR-based TP: 2.0 ATR
- Risk-based lot sizing with cost per trade

## Files
- Config: `data/strategies/gold_breakout.py`

## Backtest Status
- No backtest results this session
- Prior verified evidence through 01-08-2024 shows strong performance on GC=F proxy

## Rules
- Entry: breakout close above `high20` with weekly bias bull
- Stop: `high20 - 0.5 ATR`
- Target: `entry + 2.0 ATR`
- Risk: 0.5% per trade minimum lot
- Notes: untested in current live data path; hypothesis only
