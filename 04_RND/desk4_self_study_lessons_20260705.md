# Desk 4 — Self-Study Lessons Log
_Session: 2026-07-05 22:45 Tunis_

## Sources Audited
- `data/sprint/lane1.log`
- `data/sprint/latest_lane1_decision.md`
- `scripts/sprint_lane1_mtf_loop.py`
- `scripts/sprint_controller.py`
- `data/rnd/desk2_backtest_matrix_20260705_2301.log`

## Verified Lessons

### Lesson 4-1: Path-construction on Windows breaks decision logging
- Evidence: `OSError: [Errno 22] Invalid argument ... \sprint_decisions\2026-07-05\2026-07-05T22:05:41...md`
- Root cause: ISO timestamp with colons is illegal in Windows directory/file names.
- Fix scope: in `scripts/sprint_lane1_mtf_loop.py`, replace `:` with `-` **at full-path boundary**, not just filename metadata. Current code only sanitizes filename. **Use repo-local vault path**, not hardcoded AppData `.Hermes` path. **Prefer Markdown vault files for journaling**, JSONL for runtime decision events.

### Lesson 4-2: Lane 1 uses undefined `ts`
- Evidence: `NameError: name 'ts' is not defined. Did you mean: 'os'?`
- Root cause: `append_decision(decision)` references undefined `ts`; intended `decision.cycle_ts`.
- Fix scope: `scripts/sprint_lane1_mtf_loop.py` — pass `ts` into `append_decision` **or** reference `decision.cycle_ts` inside `append_decision`.

### Lesson 4-3: Lane 1 paper signal payload is schema-incomplete
- Evidence: `paper_signal BUY status=422 resp={detail missing instrument field}`
- Root cause: `submit_paper_trade` builds payload without `instrument:` field.
- Fix scope: `scripts/sprint_lane1_mtf_loop.py` — add `instrument: SYMBOL` to payload.

### Lesson 4-4: Paper-mode inference must be behavioral, not config-derived
- Evidence: execution service defaults to paper when signal lacks `mode`; there is no global `TRADING_MODE` gate.
- Lesson: write trade checks against actual sent fields, not assumed config keys.

### Lesson 4-5: Backtest maturity is timeframe-dependent
- Evidence: Desk 2 found real trades only on H4/M15; M1/M5/W1 untestable due data coverage.
- Lesson: Do not promote strategies from untested timeframes.

### Lesson 4-6: WA for skill patches until evidence is explicit
- Decision: no patch to `skills/hermes-trading-system` because current repo evidence shows defects in `sprint_*` scripts, not skill instructions.
