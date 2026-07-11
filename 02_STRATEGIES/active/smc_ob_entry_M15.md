---
id: smc_ob_entry_M15
name: smc_ob_entry_M15
strategy_id: smc_ob_entry_M15
instrument: BTCUSD
timeframe: M15
status: backtested_rejected
source: builtin
author: Hermes Agent
date_created: 2026-07-06
tags:
  - smc
  - order-block
  - backtested
  - rejected
```

# smc_ob_entry_M15

Order-block retest entry on BTCUSD M15.

## Backtest Evidence
- Source: `04_RND/desk2_backtest_matrix_20260705_2301.log`
- Trades: 52
- Win rate: 15.38%
- AVG win R: 1.62
- AVG loss R: 0.86
- Expectancy: -0.48R
- Max drawdown: 24.72%
- Profit factor: 0.34
- Sharpe: -18.74

## Verdict
Rejected. Negative expectancy with poor win rate and high drawdown. Retaining as monitor-only watch for structure observation only.

## Rules
- Trade: retest of identified order block after BOS/CHoCH
- Session: London preferred
- Notes: backtest evidence does not support live promotion
