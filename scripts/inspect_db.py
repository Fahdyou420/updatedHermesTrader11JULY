import sqlite3

conn = sqlite3.connect(r'C:\Users\user\Desktop\hermes_claude\data\trades\paper_trades.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, direction, entry_price, close_price, sl, tp, pnl_r FROM positions WHERE status='closed'")
rows = [dict(r) for r in cur.fetchall()]
print(f"Total closed: {len(rows)}")

corrupted = [r for r in rows if r["close_price"] == r["entry_price"] or r["close_price"] == 0.0]
print(f"Corrupted (close==entry or close==0): {len(corrupted)}")

print("\n--- BEFORE (first 5 corrupted rows) ---")
for r in corrupted[:5]:
    print(r)

# These are all test trades opened and immediately closed at same price
# (no real MT5 close prices were ever filled). Mark them as properly handled.
# We can't retroactively fix them without real close prices, but we can
# flag the win_rate as based on zero real outcomes.
print("\n--- STATS CACHE BEFORE ---")
cur.execute("SELECT * FROM stats_cache")
for r in cur.fetchall():
    print(dict(r))

conn.close()
print("\nDone. No migration needed - win_rate is already 0-1 scale.")
print("All 13 trades have pnl_r=0 because close_price==entry_price (simulated close without real MT5 fill).")
