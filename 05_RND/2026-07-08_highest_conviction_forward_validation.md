# Highest-Conviction Setup: `gold_breakout` Deep Research + Forward Validation
> 2026-07-08T?? UTC | Native MT5 MCP 7779 | XAUUSD

## 1. Current Market Snapshot from Native Endpoints
- Latest native M15 close: 4056.62 at 2026-07-08T12:05:28Z
- Latest native D1 close: 4052.04 on 2026-07-08
- D1 bullish filter: FAIL — close below EMA20 ~4105.91
- Weekly bullish flag: NO
- 30-day native paired trades: 28 pairs, net PnL -2416.69 USD, WR 50.00%, PF inf
- Account equity: 97539.62 USD | free margin: 97539.62 USD | balance: 97539.62 USD | no open positions

## 2. Live History Failure Modes
- 30-day paired outcome is net negative and PF < 1.0; this rules out live promotion for the same SMC sprint emissions.
- Loss cluster after 2026-07-06 session: current price has moved down from ~4177 to ~4050 cluster; OB range entries were invalidated by structural shift.
- Big recent SELL losses:
  - 2026-07-07 14:45:39 SELL loss -770.72 USD
  - 2026-07-08 12:05:07 SELL loss -727.68 USD
  - 2026-07-08 12:06:15 SELL loss -701.68 USD
- `bullish_ob BUY` remains watch_only: current price is below referenced OB zone; sprint emissions are not actionable.

## 3. Strategy Under Review: `gold_breakout` D1 Native Backtest
Rule set:
- weekly bullish bias required,
- Close > prior 20-bar high,
- SL = breakout high − 0.5×ATR14,
- TP = entry + 2.0×ATR14,
- round-trip cost = 0.30.

| Segment | Trades | Win Rate | Total PnL | PF | Avg Win | Avg Loss |
|---|---|---|---|---|---|---|
| Train 01/2020–05/2025 | 68 | 80.88% | +2367.59 | 20.07 | +45.30 | -9.55 |
| Holdout 06/2025–06/2026 | 19 | 84.21% | +1519.09 | 8.51 | +107.58 | -67.40 |
| Full 01/2020–06/2026 | 87 | 81.61% | +3886.68 | 12.91 | +59.34 | -20.40 |
| M15 baseline weekly bull | 22 | 63.64% | +430.26 | 12.37 | +33.44 | -4.73 |
| M15 weekly + D1 bullish | 16 | 56.25% | +261.34 | 14.22 | +31.23 | -2.82 |
| M15 weekly+D1 bull + session | 13 | 53.85% | +109.13 | 7.19 | +18.11 | -2.94 |

- All D1 variants clear long-horizon evidence after holdout validation: holdout WR 84.21%, PF 8.51.
- M15 proxy supports hypothesis but coverage is short-term; D1 remains primary.

## 4. Monthly PF Stability (D1 baseline, months with trades)
- Distinct months: 77 | months with trades: 77 | months with PF>1.15: 70 | months PF infinite: 5

## 5. Failure Modes
1. Live 30-day paired history net negative; this constrains live promotion.
2. Sprint `bullish_ob BUY` likely stale under HTF discount; not executable at current close under referenced OB zone.
3. SMC M15 finalists fail promotion gates on multiple subagent runs.
4. `analysis` endpoint returns empty; cannot verify OB/FVG.
5. Cron nightly scan fails since 2026-07-03, so sprint data is stale.

## 6. Decision
**Best research candidate: `gold_breakout` native D1.**
- Latest native D1 close is below weekly + 20-bar high conformance; no new setups active.
- Historical D1 evidence remains the only mature cleared hypothesis in routine validation.
- Trade recommendation for next forward pass: wait for next native D1 close to claim > 20-bar high against weekly bull bias; do not execute current M15 bullish_ob sprint until D1 bias is confirmed. Live promotion remains blocked.

## 7. Upgrade Plan
1. Replace proxy bars with native bars/logic; keep M15 only for confirmation/risk layering.
2. Add TP1→BE/TP2 trailing and drawdown governor.
3. Session gate London/NY windows including cutoff for session close risk.
4. Repair `scripts/cron/nightly_scan.ps1` for clean `exit 0` each night.
5. Archive native history beyond 30-day window for formation tracking.

## 8. Files Produced / Updated
- `data/rnd/xau_backtest_update_latest.json` — consolidated evidence, live history, backtest matrix.
- `05_RND/2026-07-08_highest_conviction_forward_validation.md` — this human-readable research update.
- Related evidence: `data/rnd/xau_native_history_latest.json`, `data/rnd/xau_native_d1_2000.json`, `data/rnd/xau_native_m15_2000.json`
