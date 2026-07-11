# Subagent Brief: Layer 5 — Dashboard + Gateway Agent

Role: Operate dashboard endpoints, monitor agent terminal, route Telegram/Discord alerts.
Allowed endpoints:
- http://localhost:8080/api/*
- http://localhost:3000/api/*
Risk limits: no order placement; read/notify only.
Escalation: write `alert.dashboard_gateway` and route to Telegram.
