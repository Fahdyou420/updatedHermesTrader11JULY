# OmniVision Operational Bus Contract
Shared path: `C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\Common\Files`

## Signal String Format
Write JSON files with:
```json
{
  "type": "signal",
  "timestamp": "2026-07-06T13:30:00Z",
  "agent_id": "03",
  "strategy": "OB",
  "symbol": "XAUUSD",
  "timeframe": "M15",
  "direction": "BUY",
  "price": 2334.50,
  "message": "[SIGNAL] Agent 03 (OB): Valid demand zone identified at 2334.50."
}
```

## Validator Writes
- `AI_Command.json` for pass/fail command state
- `omni-core/validators/memory/state.json` for internal validator memory

## Trade Outcomes
MT5 EA/existing pipeline writes `Trade_Outcome_<ticket>.json`.
R&D processor reads the last N outcomes and writes `omni-core/research/rd_results.jsonl`.
