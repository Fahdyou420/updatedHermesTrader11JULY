---
name: messaging-department
description: "Outbound notifications only for the Hermes trading stack. This department does not handle inbound commands. Triggers: trade opened/closed, kill switch triggered, reliability department UNVERIFIED flag."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, messaging, notifications, telegram, discord, gateway, kill-switch, reliability-flag]
---

# Messaging Department

Use this skill whenever the user asks to send alerts, notify on trade events, dispatch kill-switch messages, or surface reliability flags to external channels.

## Constraints

- Outbound only. Do not implement inbound command handling.
- Use the existing Hermes gateway integrations (Telegram/Discord) rather than building a custom notifier.
- Surface real tool evidence on sent messages where possible.

## Triggers

- Trade opened/closed: include instrument, direction, lots, entry, SL, TP, PnL, timestamp
- Kill switch triggered: include reason, affected instrument/department, timestamp
- Reliability UNVERIFIED flag: include department, claim, evidence inspected, timestamp

## Failure Behavior

If the gateway reports failure, append to the reliability department's incident log under `05_RND/reliability/incident_log.md` and do not block business logic because of notification failure.
