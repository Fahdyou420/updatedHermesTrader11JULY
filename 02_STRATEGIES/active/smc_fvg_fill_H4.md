---
id: smc_fvg_fill_H4
name: smc_fvg_fill_H4
strategy_id: smc_fvg_fill_H4
instrument: BTCUSD
timeframe: H4
status: hypothesis
source: builtin
author: Hermes Agent
date_created: 2026-07-06
tags:
  - smc
  - fvg
  - backtested
  - undersampled
```

# smc_fvg_fill_H4

Retrace into unmitigated FVG on BTCUSD H4.

## Desk 2 Evidence Base
- Trades: 2
- Win rate: 50.00%
- AVG win R: 2.01
- AVG loss R: 1.02
- Expectancy: +0.50R
- Max drawdown: 1.00%
- Profit factor: 1.97
- Source: `04_RND/desk2_backtest_matrix_20260705_2301.log`

## Verdict
Hypothesis only. Too few trades to judge. Positive expectancy and PF, but requires larger sample before promotion.

## Rules
- Trade: price retrace into unmitigated FVG with HTF alignment
- Bias: bullish FVG buy; bearish FVG sell
- Notes: keep monitor-only until sample expands
