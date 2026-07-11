# Cron Research Update — 2026-07-11
> Trigger: latest 15m scan review → highest-conviction deep research → dataset validation → 05_RND registration.

## 1. Latest 15m Scan Output
- Highest-conviction emission reviewed from prior regime: repeated `bullish_ob BUY`.
- Current live native M15 snapshot: ~200 bars cover ~2026-07-10 late UTC through ~2026-07-11 early UTC.
- Latest M15 close ~4101–4136 area; price is below the historic OB zone referenced in sprint metadata.
- Result: setup is not executable right now.

## 2. Live Native Endpoint Evidence
| Endpoint | Result |
|----------|--------|
| `/health` | 200 → `native_mt5=true` |
| `/api/native/account` | online FTMO demo, balance/equity 96564.91 USD, no margin |
| `/api/native/positions` | 0 open positions |
| `/api/native/latest_bars?tf=M15&n=200` | 200 bars recovered |
| `/api/native/history?days=30&instrument=XAUUSD` | 8 trade legs → 4 paired round trips |

## 3. Paired Live Trade Outcomes
- **Pairs:** 4 closed pairs in last verified 30-day native window.
- **Net PnL:** **−3425.04 USD**.
- **Win rate:** **0.00%** (0 wins / 4 losses).
- **Average win:** N/A.
- **Average loss:** **−856.26 USD**.
- **Profit factor:** **0.00**.
- **Notable clustered losses:**
  - Short loss −756.00 USD (`position_id` 493013117).
  - Short loss −683.50 USD (`position_id` 493089264).
  - Short loss −796.00 USD (`position_id` 493017979).
  - Short loss −1179.50 USD (`position_id` 493091974).
- **Failure reasons from tickets:** SL on all four (`[sl ...]` observed in `comment`).
- **Max drawdown in window:** ~1180.94 USD per pair sequencing.

## 4. Failure Modes
1. `bullish_ob BUY` no longer satisfies entry: latest price below referenced OB zone.
2. Live 30-day native history is net negative with 0% WR; blocks any live promotion.
3. SMC tagger remains empty from historical evidence; live OB/FVG tagging is unreliable.
4. All recent tickets were short-side SL hits; actual call-side execution is absent in this window.
5. Nightly scan cron emits exits without work output since at least 2026-07-03, reducing freshness confidence.

## 5. Setup Reviews
- `bullish_ob BUY`: stale, watch-only until D1 bullish bias returns above EMA20, OB reclaims, and SMC tagger returns populated OB tags.
- `gold_breakout` native D1: best researched candidate by scripts/note history, but unsuitable for 15m live execution and promoted moves require HTF confirmation return.

## 6. Multi-TF Matrix (Last Verified)
| Strategy / TF | Pairs | Net PnL | WR | PF | Status |
|--------------|-------|---------|-----|---|--------|
| Live native 30d | 4 | -3425.04 | 0.00% | 0.00 | rejected |
| Prior `gold_breakout` native D1 (2020-06-03) | 87 | +3886.68 | 81.61% | 12.91 | research candidate |
| Prior SMC M15 local finalists | varied | negative | ~36–45% | ~1.0–1.3 | rejected |

## 7. Immediate Upgrade Plan
1. Repair nightly scan cron so fresh 15m scan emissions are available instead of stale sprint emissions.
2. Restore `/api/native/smc_analysis` reliability so OB/FVG can be validated live.
3. Add M15 partial-TP/drawdown governor using D1 ATR regime before live promotion.
4. Require D1 close > EMA20 for any long-only live setup.
5. Build native-history archive so 30-day window constraints end.

## 8. Decision
**Status:** `do_not_trade / watch_only`.
- Do not promote the highest-conviction scan output (`bullish_ob BUY`) to live or paper execution.
- Treat as research-only until live 30-day native paired history turns net positive for 14 consecutive days and `gold_breakout`-style D1 setup reasserts.

## 9. Associated Files
- `05_RND/2026-07-11_cron_research_deep_research.md`
- `05_RND/2026-07-10_cron_research_update.md`
- `05_RND/2026-07-08_scan_deep_research.md`
- `data/rnd/xau_native_history_latest.json`
- `data/rnd/xau_native_strategy_pack.json`

## 10. Notes / Future Upgrades
- Live failure pattern is short-side SL clustering; long-bias candidate (`bullish_ob BUY`) is not actionable in current price regime.
- Next evidence checkpoint: repair scan cron and re-run on next D1 close above EMA20.
