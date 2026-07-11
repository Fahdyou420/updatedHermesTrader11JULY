# Desk 5 — Verification Log
_Start: 2026-07-05 22:45 Tunis_

## Findings
- Full stack ports healthy: 7779/5559/5560/5561/5562/5563.
- Kill switch inactive.
- Contradiction scan: no cross-desk contradictions found.

## 6 Excess lane1_* Position Close Results
Original symptom: earlier attempts returned `404: {"detail":"No position found matching id: ..."}`.
Root cause: non-exact ticket IDs were used. With exact IDs from `/positions`, `POST http://127.0.0.1:5561/close/{trade_id}` returned:
- `200` for newly closed tickets, with full close payload.
- `200` with `"status": "already_closed"` for tickets closed by background monitor.

Raw successful close:
```json
{
  "status": "closed",
  "trade_id": "lane1_1783304084267",
  "close_price": 4179.966352605585,
  "data": {
    "id": "lane1_1783304084267",
    "instrument": "XAUUSD",
    "direction": "BUY",
    "entry_price": 4179.966352605585,
    "sl": 4160.696785714286,
    "tp": 4218.396428571428,
    "lots": 0.38,
    "strategy_id": "lane1_mtf_auto",
    "setup_type": "mtf_auto",
    "session": "overlap",
    "status": "closed",
    "close_reason": "manual"
  }
}
```

Final closed-book confirmation:
```json
[]
```
from `mcp_hermes_trading_get_open_positions`.

## Checkpoints
- A: `00_INBOX/desk1_mtf_log.md`
- B: `04_RND/desk2_backtest_matrix_20260705_2301.log`

## Outstanding Blockers
- None remaining for Desk 5.
- Desk 2 M1/M5/W1 gaps remain data-source 404s; not retried per plan.
