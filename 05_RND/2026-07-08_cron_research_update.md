# Cron Research Update — 2026-07-08
> Investigation: 15m scan review → highest-conviction deep research → dataset validation → 05_RND registration

## 1. Cron Context / Evidence State
- This run is autonomous; no user clarification possible.
- Live service probe at 2026-07-08T20:21Z shows active bridges on `127.0.0.1:5561`, but `:7779/health` refuses new connection, so fresh native MCP history/positions cannot be fetched in this pass.
- Decision: do not fabricate new live numbers. Reuse the most recent verified live evidence, and add the current investigation as a timestamped research note.

## 2. Latest 15m Scan Output Summary
- Lane 1 latest decision file timestamp: `2026-07-06T10:29:52Z`.
- Highest-conviction emission in sampled window: `bullish_ob BUY` with HTF bias bullish, LTF OB reclaim trigger, M15 close ~4148.89.
- Emissions observed where `strategy_id` was missing: repeated `422` validation failures from `POST /paper_signal`, followed by successful retries with auto-generated ids.
- Bias signals from that decision: H4 ema20=4120.65, D1 ema20=4170.48, W1 HH/HL.
- Since that emission, live paired XAUUSD history shows large SELL losses clustered `2026-07-07 14:45Z` and `2026-07-08 12:05Z–12:06Z`. This makes the prior bullish_ob sprint stale and not executable at current close.

## 3. Deeper Research Findings
### 3.1 Highest-Conviction Candidate
- `gold_breakout` native D1 remains the only candidate with cleared long-horizon evidence:
  - Train `2020-01-01`–`2025-05-31`: 68 trades, WR 80.88%, PnL +2367.59, PF 20.07, avg win +45.30, avg loss -9.55.
  - Holdout `2025-06-01`–`2026-06-03`: 19 trades, WR 84.21%, PnL +1519.09, PF 8.51, avg win +107.58, avg loss -67.40.
  - Full `2020-01-01`–`2026-06-03`: 87 trades, WR 81.61%, PnL +3886.68, PF 12.91.
- M15 proxy samples support hypothesis directionally but are short-horizon and not promotion-ready.

### 3.2 Live 30-Day Native Paired History
- Last verified aggregate: 28 pairs, net PnL -2416.69 USD, WR 50.00%, avg win +647.87, avg loss -820.49, max drawdown ~6884.53 USD.
- Cluster losses: SELL -770.72, SELL -727.68, SELL -701.68.
- This window blocks live promotion for SMC sprint emissions.

### 3.3 Backtest / Forward Validation Feasibility
- `:5560/backtest` at last check returned 404/0-interest results for XAUUSD bar schedules, indicating the backtesting service path lacks populated XAUUSD bar datasets for requested TFs.
- Lane 3 forward validation log explicitly records: no qualifying strategy-TF passed criteria; no live paper promotions made from lane 2 evidence.
- Promotion gates in effect: WR ≥ 45%, PF ≥ 1.15, maxDD ≤ 4%, Pf stability ≥ 8/12 months, and require tagged lanes with sufficient trade count. None of the live/sprint emissions satisfy these in current dataset.

## 4. Failure Modes Identified
1. Live 30-day history net negative with large avg loss, while strategy history is long-horizon positive.
2. SMC sprint emissions repeat `bullish_ob BUY` without dependent live execution reliability.
3. Dashboard/live tagger endpoints return empty/zero-populated tag arrays; cannot verify OB/FVG live.
4. Backtest route `:5560` does not return XAUUSD bar-backed passes for current strategy sweeps.
5. `strategy_id` omission caused 422 paper_signal rejections; lane controller should enforce field presence before retry.

## 5. Canonical Decision
- Best research candidate: `gold_breakout` native D1.
- Live next-action: wait for next native D1 close above prior 20-bar high against weekly bullish bias before considering entry.
- Current `bullish_ob BUY` M15 sprint: watch_only / do_not_trade.
- Live promotion: blocked.

## 6. Actionable Upgrade Plan
1. Replace proxy bars with native D1 bars when available; use M15 only for confirmation/layering.
2. Add TP1 → breakeven → TP2 trailing, plus drawdown governor on 30-day net PnL.
3. Add London/NY session gating with cutoff for session-close risk.
4. Fix `strategy_id` injection before paper_signal submission to eliminate 422 noise.
5. Archive native history beyond 30 days for true formation tracking.

## 7. Files Produced / Updated This Cron
- New: `05_RND/2026-07-08_cron_research_update.md`
- Updated: `data/rnd/xau_backtest_update_latest.json`
- Updated: `data/rnd/xau_native_strategy_pack.json`

## 8. Next Cron Priorities
- Recheck `:7779/health` availability; if restored, refresh live paired history and latest D1 close.
- Verify `:5560/backtest` bar schedule population; if empty, delay lane2 rerun until bar ingestion completes.
- Continue watching for valid `bullish_ob BUY` only after D1 bias re-confirms and tagger endpoint populates.
