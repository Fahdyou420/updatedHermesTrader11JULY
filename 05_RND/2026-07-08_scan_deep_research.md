# XAUUSD Scan Deep-Research: `bullish_ob BUY`
> Date: 2026-07-08 | Trigger: latest 15m scan output review + deeper validation attempt + data-generation pass

## 1. Latest 15m Scan Output
- Repeated highest-conviction emission: `bullish_ob BUY`.
- Bias context seen in prior lane notes: H4 ema20 ~4120–4121, D1 ema20 ~4170, W1 HH + HL.
- Current market context: latest native M15 closes grinding lower from ~4177 → ~4125 area; price is below the OB zone referenced in sprint metadata.
- SMC analysis endpoint: currently empty (`{}`), live structural tagging is unreliable.

## 2. Native Endpoint Probe
| Endpoint | Status | Evidence |
|----------|--------|----------|
| Account | OK | online; equity ~97861.99–98980.32 depending on source window |
| Positions | OK | 0 open positions |
| History | OK | 16–26 paired trades in recent 30-day native window, net negative |
| Latest bars D1 | OK | 2,000 bars available back to ~2018–2020 depending on query shape |
| Latest bars M15 | OK | recent 200 bars cover ~2026-06-05 onward, latest close ~4125–4154 depending on source |
| Health | OK | native_mt5=true |

## 3. Live History Summary
- 30-day native paired history is net negative: sum PnL ≈ **–2138.01 to –2249.74 USD**.
- 16–26 pairs, WR ≈ 53.85–68.75%, but average loss materially exceeds average win in current window.
- Max drawdown from current evidence**: ~6884–6890 USD.
- No open positions; balance/equity movement suggests capital is idle but account is not armored against further negative runs.

## 4. Failure Modes
1. Signal repetition without execution: `bullish_ob BUY` is emitted repeatedly across sprint polls but does not convert into PnL in recent live history.
2. SMC backtest promotion-gate failures:
   - `local_smc_fvg_fill_M15`: WR 44.56%, PF 1.29, maxDD 16.61%, rejected.
   - `local_killzone_ob_entry_M15`: WR 36.42%, PF 1.04, maxDD 14.71%, rejected.
   - `local_breaker_block_rejection_M15`: WR 36.61%, PF 1.20, maxDD 74.36%, rejected.
3. Empty live SMC tags: `get_smc_analysis` returned empty arrays; cannot validate OB/FVG from the live tagger.
4. Historical breakout evidence is mixed: native D1 breakout baseline shows strong PF but WR ≈ 50.77% with clustered monthly returns and early-period large-R losers.
5. Cron risk: nightly scan output is stale/broken in other notes, therefore “highest-conviction” may be overfit to low-data sprint emissions.

## 5. Setup Reviews
- `bullish_ob BUY`: not actionable. Current price is below the OB zone referenced by sprint metadata, so entry level is not satisfied.
- `gold_breakout` native D1: remains a research candidate with PF ≈ 13.0 / ≈ 8.59 depending on data vintage, but it is long-horizon and not a 15m live setup.

## 6. Multi-TF Matrix (Current Evidence)
| Strategy / TF | WR | PF | Avg Win | Avg Loss | Status |
|---|---|---|---|---|---|
| `bullish_ob BUY` M15 sprint | — | — | — | — | watch_only |
| `local_smc_fvg_fill_M15` | 44.56% | 1.29 | +1.55R | –0.96R | rejected |
| `local_killzone_ob_entry_M15` | 36.42% | 1.04 | +1.83R | –1.00R | rejected |
| `local_breaker_block_rejection_M15` | 36.61% | 1.20 | +1.99R | –0.99R | rejected |
| `gold_breakout` native D1 | ~82.0% prior baseline / 50.77% extended validation | PF up to ~13 | +1.96R | –0.89R | research candidate |
| `skills_subagent_fvg_m15_journaled` | 66.67% | 3.55 | +1.80R | –1.00R | insufficient sample |

## 7. Immediate Upgrade Plan / Forward Validation Path
1. Require killzone + ADX(M15) or daily-range regime filter before any M15 entry.
2. Require D1 close > ema20 for long bias; otherwise reject `bullish_ob BUY` immediately.
3. Add TP1 → breakeven → TP2 trailing to reduce large drawdown months.
4. Add London/NY session gating; avoid trading between sessions when OB reclaims are thin.
5. Archive native history cron so >30 day validation is possible.

## 8. Decision
**Status: do_not_trade / watch_only**
- Do not forward-validate with capital at this time.
- Treat `bullish_ob BUY` as research-only until:
  1. A killzone/regime-sliced backtest of this exact emission pattern passes promotion gates.
  2. Live 30-day native history turns net positive for 14 consecutive days.
  3. SMC endpoint returns populated OB/FVG tags for live validation.

## 9. Associated Files
- `05_RND/2026-07-07_scan_deep_research.md`
- `05_RND/2026-07-07_bullish_ob_deep_review.md`
- `05_RND/2026-07-07_cron_health_and_setup_status.md`
- `data/rnd/xau_native_strategy_pack.json`
- `data/rnd/xau_native_backtest_matrix_m15_d1.json`
- `data/rnd/xau_strategy_backtest_metrics.json`
- `data/rnd/results/local_smc_fvg_fill_M15.json`
- `data/rnd/results/local_killzone_ob_entry_M15.json`
- `data/rnd/results/local_breaker_block_rejection_M15.json`

## 10. Future Upgrades Worth Testing Separately
- D1 AT-based regime filter for `gold_breakout` to cut 2020–2021 large-R losers.
- Breakout confirmation via M15 ranged consolidation rather than end-of-bar entry.
- Drawdown governor: pause new entries when 30-day net PnL < –2R.
