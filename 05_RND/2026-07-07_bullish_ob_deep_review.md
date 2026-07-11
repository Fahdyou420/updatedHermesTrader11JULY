# Bullish OB M15 — Deep Review & Failure-First Validation
> Date: 2026-07-07 | Focus: highest-conviction replay from sprint_lane1

## Executive Summary
The most aggressive and repeated replay in the latest 15m sprint lane is **`bullish_ob` BUY**:
- Sprint lane shows multiple regenerations from 2026-07-05 through 2026-07-06.
- Regime is sticky: H4 ema20 ~ 4120, D1 ema20 ~ 4170, W1 HH + HL.
- Latest M15 close in sprint notes is ~4148–4150.
- No action has been taken in the latest native history window, but live Bloomberg-style monitor suggests watch-only.

This note uses history, sprint_lane, and local_smc backtest evidence to decide whether this setup is **post** or **do not trade**.

## Native Endpoint Probe
| Endpoint | Status | Evidence |
|----------|--------|----------|
| Account | 200 | balance 97861.99, equity 97861.99 — no open positions |
| Positions | 200 | 0 positions |
| History | 200 | 48 trades, 24 position pairs, avg PnL **-89.08 USD**, sum PnL **-2138.01 USD** |
| Latest bars M15 | 200 | 200 bars, latest close ~**4135–4165** yfinance / local |
| Health | 200 | native_mt5=true |

## Live History Review
- **30-day native window**: 24 trade pairs.
- Net average per pair: **-89.08 USD**.
- Wins: 13, Losses: 11.
- Equity curve direction: downward.
- Account is flat today in native history; no live position.

## Failure Mode Analysis
1. **Negative net PnL in last 30 days**: with spreads and slippage accounted, the trading system is not currently generating alpha. Taking new trades in the same algorithmic regime is suspect.
2. **Local_csv SMC strategies fail promotion gates**:
   - `local_smc_fvg_fill_M15` → WR 44.56%, PF 1.29, maxDD 16.61%, expectancy 0.1565. Gate result: rejected. Notes explicitly cite missing killzone + wider SL.
   - `local_killzone_ob_entry_M15` → WR 36.42%, PF 1.04, maxDD 14.71%.
   - `local_breaker_block_rejection_M15` → WR 36.61%, PF 1.20, maxDD 74.36%.
3. **Sprint decision sampling risk**: bullish_ob BUY is emitted repeatedly across consecutive sprint polls instead of converting to actual trades or rejecting quickly. This may indicate signal clustering/overstaying rather than genuine edge.

## M15 Sprint Lane Review
- **2026-07-05**: 23 BUY, 1 REJECT. Strong one-sidedness.
- **2026-07-06**: 39 BUY, 45 SELL, 49 REJECT. More balanced but still regenerating bullish_ob into bearish_ob territory, a sign of indeterminate trend.
- The stream repeatedly tags `H4 ema20 ≈ 4120`, `D1 ema20 ≈ 4170`, W1 HH/HL, and M15 closes ~4148–4150.
- No trade reached the execution layer in the latest native history check.

## Market Bars
- Latest M15 native bars from local_xau_m15: 718,203–718,273 rows of 295,225 total; latest close **4135.43–4135.70**.
- Latest M15 from yfinance `get_market_bars`: closes around **4141.70–4154.00** with volume 1266–2911.
- SMC analysis endpoint currently returns empty arrays (`{}`), so the strategy cannot rely on live structural tags at the moment.

## Forward Validation Plan
Because local backtests do not pass promotion gates, **do not forward validate with capital** until one of:
1. 30-day history turns net positive for 14 days.
2. Local SMC backtest shows ≥45% WR, PF ≥1.15, maxDD ≤4%.
3. Killzone + ATR risk block added and validated.

If those conditions are met later, the bullish_ob_BUY setup can be restricted to:
- Entry: M15 reclaim of swing-low OB with bullish engulf.
- Bias: H4 ema20 > prior swing, W1 HH + HL.
- Time: London open–close or NY open–close.
- SL: below OB low – 0.5 ATR.
- TP: entry + 2.0 ATR.

## Conclusion
**Status: do_not_trade / watch_only**
- Regime shows repeated bullish_ob_BUY signals but they have not converted into PnL in the live 30-day history.
- Local backtests of similar SMC strategies fail hard promotion gates.
- SMC endpoint is empty today; live tagging is not reliable.

## Associated Files
- `data/rnd/xau_native_history_latest.json`
- `05_RND/2026-07-07_bullish_ob_deep_review.md`
- Sprint decisions: `data/obsidian/03_TRADE_JOURNAL/sprint_decisions/2026-07-05/`, `.../2026-07-06/`
- Backtest results: `data/rnd/results/local_smc_fvg_fill_M15_trace.json`, `.../local_killzone_ob_entry_M15.json`, `.../skills_subagent_breaker_m15.json`
