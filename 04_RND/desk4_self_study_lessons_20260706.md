# Desk 4 — Self-Study Lessons
_Start: 2026-07-06_

## Goal
Identify reusable lessons from the day's failures/gaps and apply skill patches only when repo evidence supports them.

## Lessons
1. Ticket-id discipline: paper trader `/close/{trade_id}` requires exact `positions.id`. Formatting/truncation causes 404s.
2. Bridge hang masking: `/close/{trade_id}` calls MT5 bridge `/latest_bars` first; if bridge path hangs, close appears hung. Confirm exact IDs and bridge path before retrying close automation.
3. Backtest endpoint contract: async backtester requires `max_trades_per_day`; MCP wrapper did not forward it today. Treat API mismatch as evidence incompleteness, not strategy failure.
4. Data-gap triage: W1/M1/M5 source gaps are repo/service coverage limits; classify separately from strategy failure.

## Skill Patch Decision
- No skill patch applied. Available repo evidence supports memoization of lessons, not code changes.
- Revisit `skills/hermes-trading-system/SKILL.md` only if a code-path fix is confirmed.
