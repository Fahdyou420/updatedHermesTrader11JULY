---
name: execution-department
description: "Top-down multi-timeframe confluence execution: HTF bias first, LTF entries aligned only with that bias, reject and log contradictions. Routes qualifying setups through the risk gatekeeper and paper_trader path. Uses native MT5 data path for all price data."
version: "0.1.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, execution, smc, ict, xauusd, mt5, paper-trading]
---

# Execution Department

Use this skill whenever the user asks to determine bias, scan for LTF entries, run the execution loop, or route setups through the risk gatekeeper and paper trading path.

## HTF→LTF Confluence Procedure

1. **HTF Bias First** — establish regime before considering entries:
   - W1 bias: close direction vs prior weekly structure.
   - D1 bias: CHOCH/BOS or key level interaction; premium/discount.
   - H4 bias: confirm tradeable direction only if it aligns with W1/D1.
   - If W1/D1/H4 are split or neutral, declare `BIAS=NEUTRAL` and do not take directional entries. Use the rejection log.

2. **LTF Entry Alignment** — only check M1/M5/M15 after HTF bias is fixed:
   - Entry checks must align with HTF bias.
   - Contradicting LTF signals are rejected and logged with reasoning.
   - Missing instrument data on any TF is treated as `INCONCLUSIVE: no_data` and stops escalation.

3. **Gatekeeper + Paper Route** — every qualifying setup must flow through:
   - Risk gatekeeper validation.
   - `paper_trader` execution path with `mode: paper`.
   - Native MT5 price/account/position data only; deprecated bridge paths are forbidden.

4. **Decision Logging** — write both decisions to the vault:
   - Taken setups: instrument, timeframe, direction, entry/SL/TP, confidence, reasoning.
   - Rejected setups: instrument, timeframe, directional conflict description, reasoning.
   - Use `#Test_OPS` and ISO timestamp in every entry.

## Native Data Policy

All price, account, and position reads must use the **native MT5 service path** from the migration department:
- Native API: `localhost:7779`
- Deprecated legacy paths must not be used for data reads.

## Rejection Policy

Reject loudly. Do not silently downgrade a failed candidate.

## Cron Triggering

This skill supports a 15-minute cron trigger that chains HTF bias into LTF alignment automatically. The cron job should call the execution loop, write the result to the vault, and stop.
