# Desk 2 — Cross-Timeframe Research Log
_Start: 2026-07-06_

## Goal
Backtest strategy cards across M1/M5/M15/H4/D1/W1 and document verified performance per timeframe.

## Safety Rule Applied
- No risk parameter changes
- No live/trusted promotion from paper tier
- Only record hypothesis + evidence; if evidence missing, state explicitly

## Verified Evidence
Source A: `04_RND/desk2_backtest_matrix_20260705_2301.log`

| Strategy | Timeframe | Trades | Win Rate | Expectancy R | Max DD % | Profit Factor | Avg Win R | Avg Loss R |
|---------|-----------|-------:|---------:|-------------:|---------:|--------------:|----------:|-----------:|
| smc_ob_entry | M15 | 52 | 15.38% | -0.48 | 24.72% | 0.34 | 1.62 | 0.86 |
| smc_ob_entry | H4 | 100 | 13.00% | -0.46 | 46.05% | 0.31 | 1.59 | 0.77 |
| smc_ob_entry | D1 | 0 | 0.00% | 0.00 | 0.00% | 1.0 | 0.00 | 0.00 |
| smc_fvg_fill | M15 | 1 | 100.00% | 2.01 | 0.00% | 201.0 | 2.01 | 0.00 |
| smc_fvg_fill | H4 | 2 | 50.00% | 0.50 | 1.00% | 1.97 | 2.01 | 1.02 |
| smc_fvg_fill | D1 | 0 | 0.00% | 0.00 | 0.00% | 1.0 | 0.00 | 0.00 |
| smc_liquidity_sweep | M15 | 0 | 0.00% | 0.00 | 0.00% | 1.0 | 0.00 | 0.00 |
| smc_liquidity_sweep | H4 | 0 | 0.00% | 0.00 | 0.00% | 1.0 | 0.00 | 0.00 |
| smc_liquidity_sweep | D1 | 0 | 0.00% | 0.00 | 0.00% | 1.0 | 0.00 | 0.00 |

M1/M5/W1: explicit data-gap responses:
- `{"detail":"No matching bar data available for symbol XAUUSD (...)"}`

## Conclusion
- No strategy promotes to Desk 3 yet.
- Only H4 `smc_fvg_fill` shows marginal positive expectancy/ PF, but `total_trades=2`, below minimum for promotion.
- MCP `run_backtest` call path currently unavailable from this session for fresh live runs; retained prior evidence, not retried further.
