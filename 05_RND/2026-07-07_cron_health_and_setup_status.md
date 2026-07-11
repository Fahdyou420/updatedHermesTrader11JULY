# Nightly Scan Status + Highest-Conviction Setup Refresh
> Date: 2026-07-07 | Focus: cron health + 15m sprint lane highest-conviction setup

## Finding 1: Nightly Scan Cron Is Broken
- The cron script `scripts/cron/nightly_scan.ps1` passes the prompt with a literal apostrophe: `Analyse today's XAUUSD price action...`.
- Hermes CLI arg parsing fails with: `invalid choice: "today's"`.
- Evidence: `HermesLogs/cron_nightly_scan.debug.log` shows repeated `exit=2` on 2026-07-03 through 2026-07-06.
- Consequence: no fresh 15m scan has been generated since at least 2026-07-03.
- Remedy: remove or escape the apostrophe in the PowerShell prompt string; verify `hermes -z "<prompt>" --skills write_market_study` exits 0 before relying on cron output.

## Finding 2: Highest-Conviction Setup Is Still `bullish_ob BUY`
- Latest sprint decisions still list `bullish_ob BUY` as the most repeated signal on 2026-07-05 and 2026-07-06.
- Bias metadata: H4 ema20 ~ 4118–4121, D1 ema20 ~ 4170–4171, W1 HH + HL.
- Latest M15 closes observed in sprint lane: ~4148–4158.
- Current yfinance M15 bars show price grinding lower from ~4150s toward 4133–4139 cluster.

## Finding 3: Setup Must Remain `watch_only`
- Live account state: balance 0.0, equity 0.0, no open positions. No execution layer is active.
- Historical native window: net negative PnL in recent recorded history.
- Local backtest promotion-gate check:
  - `local_smc_fvg_fill_M15`: WR 44.56%, PF 1.29, maxDD 16.61%. Rejected: WR < 45%, maxDD > 4%.
  - `local_killzone_ob_entry_M15`: WR 36.42%, PF 1.04, maxDD 14.71%. Rejected: PF < 1.15, maxDD > 4%.
  - `local_breaker_block_rejection_M15`: WR 36.61%, PF 1.20, maxDD 74.36%. Rejected: WR < 45%.
  - `skills_subagent_fvg_m15_journaled`: WR 66.67%, PF 3.55, maxDD 1.0%. Only 3 trades — not enough for promotion.
- SMC endpoint returns empty today, so live structural tagging is unreliable.

## Decision
- **Status: do_not_trade / watch_only**
- Do not forward-validate with capital.
- Treat `bullish_ob BUY` as research-only until:
  1. Nightly scan runs cleanly for 5 days and produces stable `bullish_ob` generations with no contradicting bearish_ob in the same session.
  2. A killzone-sliced backtest of this setup passes: WR ≥ 45%, PF ≥ 1.15, maxDD ≤ 4%.
  3. Live history turns net positive for 14 days.

## Immediate Actions
1. Fix `nightly_scan.ps1` prompt quoting.
2. Re-enable cron after one manual successful run.
3. Add a killzone/ADX filter to `bullish_ob` before next forward pass.

## Associated Files
- `HermesLogs/cron_nightly_scan.debug.log`
- `scripts/cron/nightly_scan.ps1`
- `data/rnd/results/local_smc_fvg_fill_M15.json`
- `data/rnd/results/local_killzone_ob_entry_M15.json`
- `data/rnd/results/local_breaker_block_rejection_M15.json`
- `data/rnd/results/skills_subagent_fvg_m15_journaled.json`
- `05_RND/2026-07-07_bullish_ob_deep_review.md`
