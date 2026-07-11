---
name: memory-department
description: "Institutional memory and user-profile department for the Hermes trading stack. Extracts concrete lessons from Execution and Backtester runs into MEMORY.md. Maintains USER.md as a dialectic profile of risk tolerance, instrument/session preferences, and manual-intervention patterns. Never overwrites; only appends dated entries."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, memory, profile, lessons, user-model, reliability]
---

# Memory Department

Use this skill whenever the user asks to update trading memory, log lessons from a cycle, build a user profile, review past interventions, or run memory-sync.

## Procedure

1. Read recent activity from all other departments:
   - Kanban task history/outputs for Execution, Backtester, Reliability
   - Recent backtest JSON artifacts under `data/rnd/results/`
   - Recent strategy cards under `02_STRATEGIES/active/`
   - Recent vault notes under `05_RND/` and reliability incident log
2. Extract ONE concrete, specific lesson per run. Vague lessons are rejected.
3. Append the lesson to `MEMORY.md` with an ISO timestamp and department tag.
4. Update `USER.md` dialectically:
   - Add or refine risk tolerance signals from observed lot SL behavior, drawdown reactions, intervention timing
   - Add instrument/session preferences from active strategies, scan focus, and manual corrections
   - Record any manual-intervention/correction pattern with timestamp, action, rationale
5. Never overwrite existing sections. Only append new dated entries or add new subsection bullets.

## Lesson Quality Bar

A lesson must be:
- Specific to observed behavior in this stack
- Testable or auditable later
- Dated and attributed to a department or run
Examples of acceptable: "On 2026-07-07, FVG M15 runner produced 193 trades with win_rate 0.4456; lesson: FVG fill requires killzone filter and wider OB-based SL before promotion."
Examples of rejected: "Markets are risky." "Be careful."

## USER.md Dialectic Model

Treat USER.md as a living profile:
- Risk tolerance signals: observed max daily DD acceptance, lot-sizing overrides, intervention when DD spikes
- Instrument/session preferences: which instruments are actively traded, which sessions trigger manual changes
- Correction patterns: when the user intervened, what changed, and what that implies about preferences

Add new signals as dated bullets under existing subsections. Create new subsections only when a new category is genuinely needed.

## Cron Triggering

This skill supports a 2-hour cron trigger that reads from all other departments' recent activity and appends one lesson to MEMORY.md plus any USER.md signal updates.

## Data Access

Read access to: all Kanban task results, `data/rnd/results/*`, `02_STRATEGIES/active/*`, `05_RND/**`, `05_RND/reliability/incident_log.md`, and any department skill outputs.
