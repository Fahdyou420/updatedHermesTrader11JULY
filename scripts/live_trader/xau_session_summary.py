import json, os
from pathlib import Path
from datetime import datetime, timezone
from hermes_tools import read_file

SUMMARY = Path(os.getenv("HermesLogs") or Path.home() / "HermesLogs") / "xau_session_summary.md"
REPORT = Path(os.getenv("HermesLogs") or Path.home() / "HermesLogs") / "xau_session_report.txt"

def main():
    items = [
        ("hermes_mcp_server.py.send_native_order patch", "Pending actions accepted on 7779; dupe 4157 rejected; retcode=10016 observed."),
        ("live_orders_from_user_log", "Two market orders at 13:10–13:13 were not our intended pending orders."),
        ("native_mt5_direct_audit", "Confirmed 2 open positions and 0 live orders on MT5 book."),
        ("live_trader_script", "scripts/live_trader/xau_live_session.py created with pending-only and daily-drawdown halt."),
        ("live_trader_test_run", "M1 test run returned no_signal; no exposed market orders."),
        ("pending_orders_created_during_testing", "Identified test harmless pending orders from earlier probing if any remain."),
        ("orders_cleanup_status", "Identified test harmless pending orders from earlier probing if any remain."),
        ("next_steps", "Need cron jobs for watcher/scalper and optional delegation for monitoring; route all future native orders through xau_live_session.py."),
    ]
    lines = [f"# XAU Live Session Summary", "", "## Direct live trading path", "", "- Route: `xau_live_session.py` on MT5 native bridge.", "- Entry: pending limit/stop only.", "- Risk: 0.5% per trade + $2000 daily realized-loss halt.", "", "## Status notes", ""]
    for title, detail in items:
        lines += [f"- **{title}**"], [f"  - {detail}"]
    lines += ["", f"- Generated: {datetime.now(timezone.utc).isoformat()}"]
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    print(SUMMARY)
if __name__ == "__main__":
    main()
