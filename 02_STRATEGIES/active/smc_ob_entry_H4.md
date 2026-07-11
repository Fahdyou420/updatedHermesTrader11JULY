---
id: smc_ob_entry_H4
name: smc_ob_entry_H4
strategy_id: smc_ob_entry_H4
instrument: BTCUSD
timeframe: H4
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

# smc_ob_entry_H4

Order-block retest entry on BTCUSD H4.

## Backtest Evidence
- Source: `04_RND/desk2_backtest_matrix_20260705_2301.log`
- Trades: 100
- Win rate: 13.00%
- AVG win R: 1.59
- AVG loss R: 0.77
- Expectancy: -0.46R
- Max drawdown: 46.05%
- Profit factor: 0.31
- Sharpe: -11.81

## Verdict
Rejected. Negative expectancy across 100 trades. Retaining monitor-only watch for structure observation.

## Rules
- Trade: retest of identified order block after BOS/CHoCH
- Session: London preferred
- Notes: worst drawdown of all candidates; not suitable for promotion
