# 15m Scan Deep Research — 2026-07-12

> Trigger: latest 15m scan review → highest-conviction deep research → dataset validation → 05_RND registration.

## 1. Latest 15m Scan Output

| Path | Result |
|------|--------|
| `data/rnd/xau_scan_results.json` | Native API :7779 refused on all endpoints (connection refused) |
| Fallback | Local native JSONs: `xau_d1_bars_5000.json` + `xau_m15_bars_5000.json` |
| M15 latest bar | **2026-07-10 23:45:00+00:00**, close **4113.60** |
| D1 latest bar | **2026-07-10** (same session) |

- Highest-conviction emission from prior session: `bullish_ob BUY`.
- **Result: setup is not executable right now.** Price remains below the referenced OB zone and D1 trend is bearish.

## 2. Native Endpoint Probe Evidence

| Endpoint | Result |
|----------|--------|
| `/health` | 7779 refused |
| `/api/native/account` | unreachable |
| `/api/native/positions` | unreachable |
| `/api/native/latest_bars` | unreachable; fell back to local JSONs |
| `/api/native/history?days=30&instrument=XAUUSD` | unreachable; last verified net = −3425.04 USD, 4 pairs, 0% WR (cached from 2026-07-11 strategy pack) |

## 3. Live History Summary (last verified 30-day native window)

- **Pairs:** 4 closed pairs.
- **Net PnL:** −3425.04 USD.
- **Win rate:** 0.00% (0 wins / 4 losses).
- **Profit factor:** 0.00.
- **Failure pattern:** All SHORT trades hit SL.

## 4. Backtest Results — Deeper Research (local native JSONs)

### 4.1 `gold_breakout` D1 — Forward Validation

| Window | Trades | Net PnL | WR | PF | Avg Win | Avg Loss |
|--------|--------|---------|----|----|---------|----------|
| Last 30d | 0 | 0.00 | — | — | — | — |
| Last 60d | 0 | 0.00 | — | — | — | — |
| Last 90d | 0 | 0.00 | — | — | — | — |
| Last 180d | 4 | 992.45 | 50.00% | 1.98 | 1005.00 | 508.77 |
| Last 365d | 13 | 5605.47 | 61.54% | 3.16 | 1025.31 | 519.40 |

**Observation:** No new `gold_breakout` D1 signal in the most recent 90 days. The strategy only activates 6–12 months out and then goes dormant during drawdowns.

### 4.2 `gold_breakout` D1 — Absolute Baseline (2007–2026)

- **Trades:** 199
- **Net PnL:** 17672.49
- **Win rate:** 39.70%
- **Profit factor:** 1.29
- **Max drawdown:** −8541.93
- **TP hits:** 76 | **SL hits:** 107 | **Time exits:** 16

### 4.3 `gold_breakout` M15 — Recent 5000 bars

- **M15 bars used:** 5000
- **Total trades:** 127
- **Net PnL:** −3130.19
- **Win rate:** 29.92%
- **Profit factor:** 0.86
- **Status:** `rejected` — negative edge on lower timeframe.

## 5. Multi-TF Matrix (Last Verified)

| Strategy / TF | Trades | Net PnL | WR | PF | Status |
|---------------|--------|---------|----|----|--------|
| Live native 30d | 4 | −3425.04 | 0.00% | 0.00 | rejected |
| `gold_breakout` D1 2020–2026 | 199 | 17672.49 | 39.70% | 1.29 | research_candidate |
| `gold_breakout` D1 fwd 12m | 13 | 5605.47 | 61.54% | 3.16 | research_candidate |
| `gold_breakout` D1 fwd 6m | 4 | 992.45 | 50.00% | 1.98 | research_candidate |
| `gold_breakout` D1 fwd 3m | 0 | 0.00 | — | — | dormant |
| `gold_breakout` D1 fwd 1m | 0 | 0.00 | — | — | dormant |
| `gold_breakout` M15 recent | 127 | −3130.19 | 29.92% | 0.86 | rejected |

## 6. Setup Reviews

### `bullish_ob BUY`
- Stale: price is below the historical OB zone.
- SMC tagger not returning populated OB tags.
- **Watch-only** until D1 bullish bias returns above EMA20, OB reclaims, and SMC tagger reliability is restored.

### `gold_breakout` D1
- Best-researched candidate by history and scripts.
- Confirmed positive on native 2007–2026 backtest: +17672.49 PnL, 39.70% WR, PF 1.29.
- Forward 12m: 5605.47 PnL, 61.54% WR, PF 3.16.
- Forward 6m: 992.45 PnL, 50.00% WR, PF 1.98.
- Currently dormant on D1 for the last 90 days; unsuitable for 15m live execution.

### `gold_breakout` M15
- Rejected on recent native M15 data.
- M15 timeframe does not preserve the D1 edge.

## 7. Selected Strategy + Rules

| Field | Value |
|-------|-------|
| Name | `gold_breakout` |
| Instrument | XAUUSD |
| Timeframe | D1 |
| Net PnL (2007–2026 native) | 17672.49 |
| Win rate | 39.70% |
| Profit factor | 1.29 |
| Max drawdown | −8541.93 |
| Entry | close > previous 20-bar high |
| SL | breakout_high − 0.5 × ATR14 |
| TP | entry + 2.0 × ATR14 |
| Cost | 0.30 per round-trip |

## 8. Decision

**Verdict: `do_not_trade / watch_only`**

- Do not promote the highest-conviction scan output (`bullish_ob BUY`) to live or paper execution.
- Do not promote SMC OB M15 or `gold_breakout` M15 — both are negative on recent data.
- Treat `gold_breakout` D1 as the only positive research candidate, but it is not actionable on the 15m timeframe.
- Next evidence checkpoint: repair scan cron and re-run when D1 close above EMA20 returns and SMC tagger becomes reliable.

## 9. Immediate Upgrade Plan

1. Replace proxy with native bars when available.
2. Add H4 + D1 confluence before considering live entry.
3. Add TP1 → breakeven → TP2 trailing.
4. Add London/NY session gating.
5. Build native-history archive so 30-day window constraint ends.
6. Repair nightly scan cron for fresh 15m emissions.
7. Restore `/api/native/smc_analysis` reliability.

## 10. Associated Files

- `05_RND/2026-07-12_scan_deep_research.md`
- `data/rnd/deep_research_2026-07-12_results.json`
- `data/rnd/xau_d1_bars_5000.json`
- `data/rnd/xau_m15_bars_5000.json`
- `data/rnd/xau_scan_results.json`

## 11. Notes / Future Upgrades

- Live failure pattern is short-side SL clustering; long-bias candidate (`bullish_ob BUY`) is not actionable in current price regime.
- The `gold_breakout` D1 baseline shows a positive expectancy edge but requires D1 timeframe execution — incompatible with current 15m scanner output.
- Next step: enable H4 shift-up promotion. When D1 confirms bullish breakout, switch to H4 execution with same ATR-based SL/TP.
- Nightly scan cron has been emitting exits without fresh work since at least 2026-07-03. Must be repaired before scan can be treated as reliable emission source.
- Native MT5 service at :7779 currently refuses connections; local bar JSONs are the safest source for backtesting until service is restored.
