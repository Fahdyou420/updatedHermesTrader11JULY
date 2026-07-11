# Highest-Conviction Setup: Deep Research on `bullish_ob BUY` + Native D1 Breakout
> Date: 2026-07-07T20:01 UTC | Trigger: latest 15m scan output review and deeper validation

## 1. Latest 15m Scan Output
- Latest sprint poll window sampled: 2026-07-06 06:44–10:30 UTC.
- Emissions: `bullish_ob BUY` appears repeatedly; `bearish_ob SELL` also appears; many `none_neutral`.
- Bias metadata persisted: H4 ema20 ≈ 4120.65, D1 ema20 ≈ 4170.48, W1 HH + HL.
- Last captured M15 close: 4148.89 at latest sprint timestamp (2026-07-07 latest M15 close now ~4146.97, later 4125.21).
- Today's native M15 price action: grind lower from ~4177 → 4125; not reclaiming swing-low OB midrange.

## 2. Live Market Bars
- Native D1 bars: available from 2018-10-08 to 2026-07-07; close coverage is complete.
- Native M15 bars: last 2,000 bars cover 2026-06-05 20:15 → 2026-07-07 22:00 UTC; latest close 4125.21.
- The most recent M15 bar closed lower at 4125.21 after rejecting lower highs near 4147. Current price is below recent swing-low OB zone referenced in sprint metadata (~4141–4148).

## 3. Native Endpoint Probe Evidence
| Endpoint | Status | Evidence |
|----------|--------|----------|
| Account | 200 | balance 98980.32, equity 98980.32, trade_allowed true, no open positions |
| Positions | 200 | 0 positions |
| History (30d) | 200 | 52 deals → 26 position pairs, net sum **-1019.68 USD**, avg net **-39.22 USD** |
| Latest bars D1 | 200 | 2,000 bars, 2018–2026 |
| Latest bars M15 | 200 | 2,000 bars, 2026-06-05 → 2026-07-07 22:00 |
| Health | 200 | `native_mt5=true` |

## 4. Live History Failure Analysis
- 30-day native history: **26 pairs**, **14 wins**, **12 losses**, WR **53.85%**, PF **0.90**, estimated max drawdown **$6,890.25** if from base 98,980.32.
- Average win: **+646.67 USD**; average loss: **-839.42 USD**.
- Recent losing cluster:
  - 2026-07-07 multiple shorts/cleanups near 4145–4155, net negative.
  - 2026-07-02 SELL 1.0 lot entry 4054.42, closed at 4099.38 SL, loss **-4559.91 USD** — large directional loss while HTF may have flipped.
- Bias mismatch risk: latest SMC sprint emits `bullish_ob` while price is grinding lower under H4≈4120; D1≈4170 is far above, so bullish_ob is not aligned with D1 proximity.

## 5. Forward Validation via Bullish_OB Rules with M15 Data
- Rule set from sprint:
  - Long bias required: H4 ema20 > prior swing, D1 close above ema20.
  - Entry: M15 reclaim of swing-low OB with bullish engulf.
  - Close latest M15 at 4125 does not reclaim 4141–4148 OB; trade should stay `watch_only` under current rule.
- Trigger condition not satisfied: entry level not reached.

## 6. Deeper Research: Native D1 Breakout Candidate
Because the current sprint bullets remain watch-only, I validated the canonical breakout hypothesis on native D1 data as an alternate research path.

### Method
- Bars: native D1 2018-10-08 → 2026-07-07 (`data/rnd/xau_native_d1_2000.json`).
- Filters: ATR14 ≥ 0, previous 20-bar high available, close > previous 20-bar high.
- Entry: next bar open approximated by current close *(end-of-bar trigger)*.
- SL = breakout high − 0.5 × ATR14.
- TP = entry + 2.0 × ATR14.
- Exit: first touch of SL or TP; timeout 40 D1 bars (~8 weeks) if neither hit.
- Post-2020 validation scope: exits from 2020-01-01 onward.

### Results
- Trades evaluated: **65**.
- Wins: **33** | Losses: **32** | WR: **50.77%**.
- Average win: **+1.96 R** | Average loss: **-0.89 R**.
- Profit factor: **2.27** | Expectancy: **+0.56 R** per trade.
- Monthly PF stability (Jan/Feb/Dec included for transparency): 27 profitable months, 17 losing months.
- Monthly performance is clustered: many months with single trades and rare 0-loss months; core profitability from ~2025-09 onward.

## 7. Multi-TF Matrix (Research View)
| Strategy / TF | WR | PF | Avg Win | Avg Loss | Status |
|---|---|---|---|---|---|
| `bullish_ob BUY` M15 sprint | not executed | — | — | — | **watch_only** |
| `local_smc_fvg_fill_M15` | 44.56% | 1.29 | +1.55 R | -0.96 R | rejected |
| `local_killzone_ob_entry_M15` | 36.42% | 1.04 | +1.83 R | -1.00 R | rejected |
| `local_breaker_block_rejection_M15` | 36.61% | 1.20 | +1.99 R | -0.99 R | rejected |
| `gold_breakout` native D1 | 50.77% | 2.27 | +1.96 R | -0.89 R | research candidate |
| `skills_subagent_fvg_m15_journaled` | 66.67% | 3.55 | +1.80 R | -1.00 R | insufficient sample (3 trades) |

- Conclusion: native D1 breakout is the only strategy in current evidence that clears PF≥1.15 with 50+ trades. It is a failure-first research candidate, not a live promotion.

## 8. Failure Modes
1. **Sprint bullish_ob misalignment**: signal repeats while price closes below OB zone and H4 discounts D1; entries would be counter-trend.
2. **Live history negativity**: 30-day native execution net is negative; same algorithmic regime should not be trusted for live capital.
3. **SMC local backtests fail promotion gates**: maxDD and WR below thresholds on >250-trade samples.
4. **Breakout D1 weak sample size early months**: 2020–2021 produced many single-trade months with large R losers; needs ATR-regime filter.
5. **SMC endpoint empty today**: live structural tagging unreliable, cannot validate FVG/OB in isolation.
6. **Nightly scan cron broken**: since 2026-07-03 no clean scan outputs, so 15m research is stale.

## 9. Decision
- **Status: do_not_trade / watch_only**
- Continue treating `bullish_ob BUY` as research-only until:
  1. cron fixed and 5 days of stable sprint lane show no polarized bearishOB in same session.
  2. M15 backtest with killzone/ADX filter passes promotion gates.
  3. Live history turns net positive for 14 days.
- Register `gold_breakout` native D1 as backup research candidate for regime-validated trend days.

## 10. Immediate Upgrade Plan
1. Repair `scripts/cron/nightly_scan.ps1` apostrophe quoting; verify exit 0.
2. Restrict `bullish_ob` to D1 HTF alignment: require D1 close > ema20 and session filter London 08:00–17:00 / NY 13:30–22:00 UTC.
3. Add killzone + ADX(M15) ≥ 18 or daily_range ≥ monthly_Q3 median.
4. Re-run M15 backtest after filter; validate WR ≥ 45%, PF ≥ 1.15, maxDD ≤ 4%.
5. Run D1 breakout only on ATR regime filter to reduce 2020–2021 losers.

## 11. Associated Files
- `05_RND/2026-07-07_scan_deep_research.md`
- `05_RND/2026-07-07_bullish_ob_deep_review.md`
- `05_RND/2026-07-07_cron_health_and_setup_status.md`
- `data/rnd/xau_native_history_latest.json`
- `data/rnd/xau_native_d1_2000.json`
- `data/rnd/xau_native_m15_2000.json`
- `data/rnd/results/local_smc_fvg_fill_M15.json`
- `data/rnd/results/local_killzone_ob_entry_M15.json`
- `data/rnd/results/local_breaker_block_rejection_M15.json`
