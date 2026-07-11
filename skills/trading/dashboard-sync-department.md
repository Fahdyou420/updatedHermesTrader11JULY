---
name: dashboard-sync-department
description: "Audits whether backend system events are represented on the Hermes dashboards (:3000 and :8080). This department does not implement every feature; its job is gap detection and surfacing missing dashboard visibility."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, dashboard, sync, audit, react, flask, redis, visibility]
---

# Dashboard Sync Department

Use this skill whenever the user asks to verify dashboard visibility, audit backend event representation on :3000/:8080, or flag events with no dashboard counterpart.

## Core Mandate

Every backend event worth knowing about should have a Redis publish AND a visible dashboard consumer. This department verifies that invariant; it does not implement front-end features automatically.

## Audit Procedure

1. Define the event window, typically the last 6 hours.
2. Collect backend events from all departments' recent outputs:
   - New trades/positions
   - New strategy cards or status changes
   - Reliability flags / UNVERIFIED markers
   - Kill-switch triggers
   - Backtest result artifacts
3. Check what is actually visible on:
   - React dashboard expected at `:3000`
   - Flask dashboard expected at `:8080`
4. For each event, record:
   - `event_id`
   - `department`
   - `description`
   - `dashboard_3000_present: true|false|unreachable`
   - `dashboard_8080_present: true|false|unreachable`
   - `verdict: confirmed|missing|unreachable`
5. Write findings under `05_RND/dashboard_sync/<UTC_DATE>.md`.
6. Any `missing` finding becomes a Kanban task for the relevant department with `dept:frontend` semantics.

## Data Sources

Read access to:
- `02_STRATEGIES/active/`
- `data/rnd/results/`
- `05_RND/reliability/incident_log.md`
- Dashboard endpoints/services reachable from the host
- Redis pub/sub or equivalent state source if exposed

## Non-Goals

Do not auto-route fixes to execution code. This department audits and reports; implementation belongs to the execution or platform department.
