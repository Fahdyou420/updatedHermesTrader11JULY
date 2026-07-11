---
name: reliability-department
description: "Independent reliability and QA department for the Hermes trading stack. Verifies claims from other departments against raw logs/data, runs full-stack health checks, flags contradictions, maintains incident log, and can mark outputs UNVERIFIED if claims cannot be confirmed."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, reliability, qa, audit, incident-log, verification]
---

# Reliability Department

Use this skill whenever the user asks to verify backtest claims, audit trading stacks, run reliability/QA cycles, maintain incident logs, or validate that stated results match raw evidence.

## Core Mandate

Verify independently. Do not trust other departments’ self-reported status. Check raw artifacts directly and record the honest outcome.

## Authority

- Read access to all department logs, Kanban task results, Obsidian strategy cards, backtest JSON artifacts, and stack health endpoints.
- Explicit authority to mark any output from another department as `UNVERIFIED - disputed` when the underlying evidence cannot be confirmed.
- Must not be gated on other departments’ success/failure; reliability checks run on their own schedule.

## Verification Protocol

1. **Claim collection**: identify recent claims made by Backtester, Execution, or other departments.
2. **Evidence gathering**: read the cited JSON, Markdown, logs, or endpoints referenced in the claim.
3. **Cross-check**: compare claim wording versus raw evidence.
4. **Verdict**: record `confirmed`, `disputed`, or `no_evidence`.
5. If disputed: write `UNVERIFIED - disputed` on the output and append to the incident log.

## Full-Stack Health Checks

Run these on every cycle and record results:
- `mcp_hermes_trading_get_system_status` or equivalent native service health
- MT5 native API availability
- Backtester service responsiveness
- Paper trader service responsiveness
- Kanban dispatcher health
- Any non-`ok` status is flagged in the reliability log

## Contradiction Detection

When two departments disagree on the same data point (e.g., Backtester says win_rate=0.61 but Execution’s journal shows 0.58), flag both outputs and create an incident entry. Do not auto-resolve; surface it for human review.

## Incident Log

Maintain `05_RND/reliability/incident_log.md` with:
- ISO timestamp
- Department/claim reference
- Evidence inspected
- Verdict
- Owner/reviewer

## Cron Triggering

This skill supports a 30-minute cron trigger that runs independent of other departments’ task chains. The cron job must call the reliability check, write the result to the vault, and stop. It must not wait on Backtester or Execution tasks.

## Data Policy

All live data reads should use the native MT5 service path. Do not use deprecated legacy bridge paths for live checks. Local historical data may be checked from `data/market_data/` and `data/rnd/results/`.
