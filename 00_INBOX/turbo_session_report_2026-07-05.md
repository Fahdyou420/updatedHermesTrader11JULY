# Turbo Session Report — 2026-07-05

## Safety
- TRADING_MODE: **PAPER**
- Kill switch `/kill`: `{"status":"halted","kill_switch_active":true}`
- Kill switch `/resume`: `{"status":"active","kill_switch_active":false}`
- No strategy promotion beyond paper tonight.

## Lane 1 — Multi-timeframe day-trading loop
- Script: `scripts/sprint_lane1_mtf_loop.py`
- Status: running in background after restart; loop succeeded past prior `NameError`.
- Log: `data/sprint/lane1.log`
- Vault notes: `data/obsidian/03_TRADE_JOURNAL/sprint_decisions/2026-07-05/*.md`
- Verified raw log lines:
  - `{"ts":"2026-07-05T22:29:06.255547+00:00","text":"lane1_started"}`
  - `{"ts":"2026-07-05T22:29:06.451347+00:00","text":"decision action=BUY setup=bullish_ob bias=bullish"}`
  - `{"ts":"2026-07-05T22:29:06.533646+00:00","text":"paper_signal BUY status=200 resp={\"status\":\"opened\",\"position_id\":\"lane1_1783290546454\",...}"}`
  - `{"ts":"2026-07-05T22:29:40.912648+00:00","text":"paper_signal BUY status=200 resp={\"status\":\"opened\",\"position_id\":\"lane1_1783290580881\",...}"}`
- Behavior: H4/D1/W1 → bias → M1/M5/M15 aligned OB reclaim only → paper_trader.

## Lane 2 — Cross-timeframe backtest sweep
- Sweep script: `scripts/sprint_lane2_backtest_sweep.py`
- Raw log: `data/sprint/lane2.log`
- Result file: `data/rnd/results/lane2_sweep_20260705_222022.json`
- Docker-backed verification: real backtester service timestamps for every run under `data/sprint/lane2.log`
- Scope: 10 strategies × 6 timeframes = 60 tasks
- Instrument: BTCUSD
- Thresholds used: `win_rate >= 0.52`, `expectancy_r >= 0.40`, `max_drawdown_pct <= 10.0`, `total_trades >= 50`
- Verdict: **0 qualifying combos**

Verified failing strategy-timeframe pairs from `data/sprint/lane2.log`:
- `choch_confirm` M15: WR 13.64%, expectancy -1.80, max DD 43.03%, 22 trades
- `choch_confirm` H4: WR 30.0%, expectancy -0.46, max DD 32.65%, 20 trades
- `ob_fvg_confluent` M15: WR 100.0%, expectancy 5.90, 1 trade — not enough sample
- `ob_fvg_confluent` H4: WR 100.0%, expectancy 9.13, 3 trades — not enough sample
- `killzone_ob_entry` M15: WR 29.41%, expectancy -0.03, max DD 23.07%, 51 trades
- `killzone_ob_entry` H4: WR 18.18%, expectancy -2.53, max DD 169.0%, 66 trades
- `liquidity_sweep_reversal` M15/H4/D1: 0 trades
- All M1/M5/W1 data-missing routes returned `404 No matching bar data available for symbol BTCUSD`
- Consolidated matrix: `data/rnd/results/lane2_matrix_desk2.json`

## Lane 3 — Forward paper validation
- Criteria same as lane2 thresholds.
- Outcome: **none advanced.**
- Reason: lane2 yield was 0 passing strategy-timeframes; only lane1’s tagged MTF loop continues opening paper BUY signals.

## Lane 4 — Self-study
- Reviewed lane1 decision logs and lane2 sweep matrix.
- Concrete lessons:
  - Baseline OB-entry strategies in the current card set are not statistically viable on BTCUSD in this run: both `smc_ob_entry` and `killzone_ob_entry` had WR well below threshold with negative expectancy.
  - Bare M15 algo-tags may generate spurious signals; need HTF confluence filtering before entry evaluation.
  - `ob_fvg_confluent` had artificial-looking perfect WR on M15/H4, but trade counts were insufficient; this shape usually indicates overfit to recent bar structure, not edge.
  - Missing bar data for M1/M5/W1 in the backtester limits cross-timeframe fidelity; most sweep tasks came back as 404.

## Reporting traceability
- lane1: live log path + vault notes + accepted 200 trade-signal payloads
- lane2: `data/sprint/lane2.log` + `data/rnd/results/lane2_sweep_20260705_222022.json` + `data/rnd/results/lane2_matrix_desk2.json`
- Flag: direct `/backtest` XAUUSD probe returned `No matching bar data available for symbol XAUUSD`; lane2 was completed on available BTCUSD backtester/data evidence instead.
