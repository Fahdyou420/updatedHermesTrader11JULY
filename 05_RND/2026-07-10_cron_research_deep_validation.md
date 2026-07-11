# Cron Research Update — 2026-07-10
> Trigger: review latest 15m scan emission, deeper validation, register findings in Obsidian `05_RND/`.

## 1. Latest 15m Scan Output
- Highest-conviction emission: `bullish_ob BUY`.
- Not actionable: latest available native M15 data ends around 2026-07-08 early UTC, close ~4125–4154 depending on source.
- SMC analysis endpoint returns empty arrays from native `smc_analysis` HTTP route: cannot verify live OB/FVG tags.

## 2. Native Endpoint Probe
- Service unavailable in this run: `:7779/health` refused.
- This run's live evidence comes from the most recent verified dataset files generated on 2026-07-08:
  - `data/rnd/xau_native_history_latest.json`
  - `data/rnd/xau_native_strategy_pack.json`
  - `05_RND/2026-07-08_scan_deep_research.md`
  - `05_RND/2026-07-08_highest_conviction_forward_validation.md`

## 3. Last Verified Live 30-Day Paired History
- Best verified window: eight paired trades.
- Net PnL: **−3435.09 USD**
- Win rate: **0.00%**
- Notable clustered SELL losses around 2026-07-08; no open positions.
- Account balance / equity: **96564.91 USD** FTMO demo, no margin used.

## 4. Failure Modes
1. `bullish_ob BUY` is stale under HTF discount: price is below referenced OB zone.
2. Live 30-day history is net negative with 0% WR; blocks live promotion for any sprint emission.
3. SMC live tagger is empty; no way to validate OB/FVG from native endpoint.
4. Nightly scan cron is broken since 2026-07-03 with `EXIT=2`; sprint data may be stale.
5. Diagnostic scan attempted against `gemini-2.5-flash-preview-05-20` and flipped `do_not_trade` without tool use; intentional tool discipline was too loose and generated pointless shell loops. Principle violated: must use actual skill/MCP tools, not speculative `/scan` calls.

## 5. Backtest / Dataset Status
- Local broker CSV exports exist under `data/rnd/gold_export/`:
  - M15: 295,224 bars through 2026-06-18
  - H4: 19,233 bars
  - D1: 3,217 bars
- Current ledger notes only support `gold_breakout` as a mature candidate, not an executable 15m live setup.
- Direct CSV-backed forward-validation backtest was attempted but produced internal session errors; absent clean artifact, this run does not retry.

## 6. Decision
- `bullish_ob BUY`: **watch_only / do_not_trade**
- Best research candidate for future promotion: **`gold_breakout` native D1**, once D1 bias reasserts and live history turns net positive.
- Immediate action: **notrade / archive / repair**.

## 7. Immediate Upgrade Plan
1. Repair nightly scan cron for reliable fresh sprint emissions.
2. Restore `/api/native/history` and `/api/native/smc_analysis` reachability.
3. Add M15 partial-TP validation policy against verified broker CSV export for any future candidate.
4. Add drawdown governor pause when 30-day net PnL < −2R.

## 8. Associated Files
- `05_RND/2026-07-10_cron_research_update.md`
- `05_RND/2026-07-08_highest_conviction_forward_validation.md`
- `05_RND/2026-07-08_scan_deep_research.md`
- `data/rnd/xau_native_history_latest.json`
- `data/rnd/xau_native_strategy_pack.json`

## 9. Notes / Future Upgrades
- DSLR-style ISS data not relevant here; user's mention is unrelated to this XAUUSD workflow.
- Do not issue `bullish_ob BUY` live until:
  - D1 close > EMA20,
  - live SMC `/smc_analysis` returns populated OB/FVG tags,
  - 30-day native paired history is net positive for 14 consecutive days.
