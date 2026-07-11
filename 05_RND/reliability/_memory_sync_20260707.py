from pathlib import Path
from datetime import datetime, timezone

now = datetime.now(timezone.utc).isoformat()
repo = Path('C:/Users/user/Desktop/hermes_claude')

# Read current state before mutation
memory_before = (repo / 'MEMORY.md').read_text(encoding='utf-8')
user_before = (repo / 'USER.md').read_text(encoding='utf-8')

# MEMORY lesson
memory_entry = (
    f"<!-- {now} — memory-department sync cycle 1 -->\n"
    f"- lesson: On {now[:10]}, candidate-intake finished for gold_breakout, smc_fvg_fill_H4, smc_ob_entry_H4, smc_ob_entry_M15. "
    f"gold_breakout data-availability-check INCONCLUSIVE because data/market_data/XAUUSD_D1*.json is missing. "
    f"smc_fvg_fill_H4 trace shows 193 trades, win_rate=0.4456, expectancy_r=0.1565, max_drawdown_pct=16.61, status=rejected. "
    f"gold_breakout strategy card remained hypothesis while raw artifact exists with 0 trades; reliability marked it UNVERIFIED - disputed. "
    f"Rule: candidate-intake must verify card status aligns with artifact presence before run-backtest.\n"
    f"- source_departments: [candidate-intake, data-availability-check, reliability-check]\n"
    f"- tags: memory, lesson, 2026-07-07\n"
)

# USER signal update
user_entry = (
    f"<!-- {now} — memory-department sync cycle 1 -->\n"
    f"- observed_preference: In-depth per-trade journaling with timestamps and #Test_OPS required; 0-trade and fabricated results rejected. "
    f"Kanban + cron required over delegate_task for survivability across restarts. "
    f"No explicit risk-tolerance override observed yet; intervention pattern is process-integrity enforcement, not parameter changes.\n"
    f"- risk_tolerance_signals: daily_trailing_dd_limit=4%, max_trailing_dd_limit=8%, account_size=100000, leverage=1:100, spread_assumption=50-60, reject_empty_metrics=true\n"
    f"- instrument_session_signals: primary_instrument=XAUUSD, secondary=BTCUSD, active_timeframes=[D1,H4,M15], chart_session_channels=[M1,M5]\n"
    f"- intervention_patterns: 2026-07-07 demanded exact raw evidence instead of summaries; demanded pinned skills and durable kanban/cron wiring; demanded end-to-end manual verification\n"
    f"- tags: user, profile, 2026-07-07\n"
)

memory_after = memory_before.rstrip() + "\n\n" + memory_entry
user_after = user_before.rstrip() + "\n\n" + user_entry

(repo / 'MEMORY.md').write_text(memory_after, encoding='utf-8')
(repo / 'USER.md').write_text(user_after, encoding='utf-8')

print('MEMORY.md before lines:', memory_before.count('\n'))
print('MEMORY.md after lines:', memory_after.count('\n'))
print('USER.md before lines:', user_before.count('\n'))
print('USER.md after lines:', user_after.count('\n'))
print('SYNC_CYCLE_COMPLETE', now)
