# Cron Research Update — 2026-07-10T11:18Z
> Investigation: 15m scan review → highest-conviction deep research → dataset validation → 05_RND registration

## 1. Scan Review Source
- Reviewed `05_RND/2026-07-08_scan_deep_research.md`, `2026-07-08_highest_conviction_forward_validation.md`, and `2026-07-08_cron_research_update.md`.
- Latest 15m scan highest-conviction emission: repeated `bullish_ob BUY`.
- Latest verified native M15 close: ~4125–4154 (2026-07-08T12:05Z).
- Current status of `bullish_ob BUY`: not executable because latest close is below the referenced OB zone.

## 2. Native Service Health
- `:7779/health` refused in this cron run: cannot fetch fresh native endpoint reads.
- Evidence for this report is based on the most recent verified dataset files generated on 2026-07-08.

## 3. Validated Backtest Evidence (Dataset-backed)
- `gold_breakout` native D1 remains the only mature cleared hypothesis:
  - Train `2020-01-01`–`2025-05-31`: 68 trades, WR 80.88%, PnL +2367.59, PF 20.07, avg win +45.30, avg loss -9.55.
  - Holdout `2025-06-01`–`2026-06-03`: 19 trades, WR 84.21%, PnL +1519.09, PF 8.51, avg win +107.58, avg loss -67.40.
  - Full `2020-01-01`–`2026-06-03`: 87 trades, WR 81.61%, PnL +3886.68, PF 12.91.
- M15 proxy samples:
  - Weekly bull + D1 bull + session: 13 trades, WR 53.85%, PnL +109.13, PF 7.19.

## 4. Live 30-Day Native Paired History (Last Verified)
- 28 pairs, net PnL -2416.69 USD, WR 50.00%, PF `inf`.
- Average win +647.87, average loss -820.49.
- Max drawdown ~6884.53 USD.
- No open positions.
- Clustered losses:
  - 2026-07-07 14:45:39 SELL loss -770.72 USD (position_id 489689043)
  - 2026-07-08 12:05:07 SELL loss -727.68 USD (position_id 490854216)
  - 2026-07-08 12:06:15 SELL loss -701.68 USD (position_id 490855394)

## 5. Failure Modes
1. Live 30-day history net negative; blocks live promotion for SMC sprint emissions.
2. `bullish_ob BUY` is stale under current HTF discount and below OB zone.
3. SMC M15 finalists fail promotion gates.
4. `:7779` unavailable in this cron run; no live refresh of history or bars.
5. Nightly scan script is broken; script invokes `hermes` CLI with positional `workdir`, which causes exit code 2 due to argument parsing error.

## 6. Decision
- Best research candidate: `gold_breakout` native D1.
- Current `bullish_ob BUY`: watch only / do not trade.
- Live promotion: blocked.
- Next action: wait for next native D1 close to claim > prior 20-bar high against weekly bullish bias. Re-validate only after live history turns net positive for 14 consecutive days and `:7779` becomes reachable in a future health check.

## 7. Upgrade Plan
1. Replace proxy bars with native bars when available; keep M15 only for confirmation/layering.
2. Add TP1 → breakeven → TP2 trailing and drawdown governor.
3. Add London/NY session gating.
4. Repair `scripts/cron/nightly_scan.ps1` so `hermes` invocation parses correctly on Windows.
5. Archive native history beyond 30 days for true formation tracking.

## 8. Files Produced / Updated This Cron
- New: `05_RND/2026-07-10_cron_research_update.md`
- Existing evidence retained in:
  - `data/rnd/xau_native_strategy_pack.json`
  - `data/rnd/xau_backtest_update_latest.json`
  - `data/rnd/xau_native_history_latest.json`
  - `data/rnd/xau_native_d1_2000.json`
  - `data/rnd/xau_native_m15_2000.json`
