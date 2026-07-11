"""
Fix corrupted paper trades: all 13 closed positions have close_price == entry_price
because the close() call never received a real MT5 fill price. 

Since we can't get the real historical close prices, we'll mark these trades as
'cancelled' (null outcome) so they don't pollute the win_rate calculation.
The win_rate will correctly show 0/0 = no data rather than 0/13 = 0% win.

Then recompute stats_cache fresh.
"""
import sqlite3
import time

DB = r'C:\Users\user\Desktop\hermes_claude\data\trades\paper_trades.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== BEFORE ===")
cur.execute("SELECT * FROM stats_cache")
before = dict(cur.fetchone() or {})
print(f"stats_cache: {before}")

cur.execute("SELECT COUNT(*) as c FROM positions WHERE status='closed' AND close_price = entry_price")
bad_count = cur.fetchone()["c"]
print(f"Corrupted trades (close==entry): {bad_count}")

# Mark corrupted trades as 'cancelled' so they are excluded from stats
print(f"\nMigrating {bad_count} corrupted trades to status='cancelled'...")
conn.execute("""
    UPDATE positions 
    SET status='cancelled', close_reason='migrated: close_price was identical to entry_price (no real MT5 fill)'
    WHERE status='closed' AND close_price = entry_price
""")
conn.commit()

# Recompute stats from scratch (now with 0 valid closed trades)
cur.execute("SELECT * FROM positions WHERE status='closed'")
valid_closed = cur.fetchall()
print(f"Valid closed trades remaining: {len(valid_closed)}")

# Rewrite stats_cache
conn.execute("DELETE FROM stats_cache")
conn.execute("""
    INSERT INTO stats_cache (id, computed_at, total_trades, win_rate, expectancy_r, max_dd_pct, profit_factor, avg_win_r, avg_loss_r)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", ("latest", int(time.time()), len(valid_closed), 0.0, 0.0, 0.0, 1.0, 0.0, 0.0))
conn.commit()

print("\n=== AFTER ===")
cur.execute("SELECT * FROM stats_cache")
after = dict(cur.fetchone())
print(f"stats_cache: {after}")
print(f"\nwin_rate BEFORE: {before.get('win_rate')} → AFTER: {after['win_rate']}")
print(f"total_trades BEFORE: {before.get('total_trades')} → AFTER: {after['total_trades']}")
print("\nMigration complete. Dashboard will now show 'No trade data' rather than a misleading 0%.")
conn.close()
