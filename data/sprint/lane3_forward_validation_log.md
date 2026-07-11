# Lane 3 Forward Paper Validation — 2026-07-06

## Criteria
- Same lane2 thresholds: `win_rate >= 0.52`, `expectancy_r >= 0.40`, `max_drawdown_pct <= 10.0`, `total_trades >= 50`
- Promotion rule: **none** unless explicit user review clears the trust tier.
- Tag requirement: lane1 vs lane3 positions must be distinguishable.

## Source evidence
- Lane 2 result files: `data/rnd/results/lane2_sweep_20260705_222022.json`
- Lane 2 log: `data/sprint/lane2.log`
- Lane 2 consolidated matrix: `data/rnd/results/lane2_matrix_desk2.json`

## Lane 2 outcome
- Total tasks: 60
- Passed: 0
- Notable passes-looked-close-but-failed:
  - `ob_fvg_confluent` BTCUSD M15/H4: perfect WR, but trade counts 1 and 3 => not enough sample
  - `killzone_ob_entry` BTCUSD M15: 51 trades but WR 29.41% and expectancy -0.03 => fails

## Lane 3 verdict
- **No strategy-timeframe qualifies** for forward validation.
- **No live paper promotions made** from lane 2 evidence.
- Lane 1 remains the only active forward paper lane for this sprint.

## Separate tagging / log integrity
- All observed live lane1 paper positions are tagged `setup_type: mtf_auto` and `strategy_id: lane1_mtf_auto`.
- Verified by `http://127.0.0.1:5561/positions` raw JSON:
  - `lane1_1783290546454` ... `open_time=1783290546` ... status=open
  - `lane1_1783290580881` ... `open_time=1783290580` ... status=open
  - additional lane1 IDs through `lane1_1783303197712` with status=open
- Additional non-lane1 artifact seen: `qa_post_resume_1` (`strategy_id=qa_strat`, `setup_type=smoke`) present in paper positions; this is test QA state, not lane3 validation data.
- Lane1 vault decision files are present under: `data/obsidian/03_TRADE_JOURNAL/sprint_decisions/2026-07-05/*.md`
- Integrity conclusion: lane1 outputs are intact and distinguishable from any QA smoke state.

## Lane 3 status
- Gated by lane2 outcome.
- Reopen only after new lane2-passing strategy-timeframe exists.
