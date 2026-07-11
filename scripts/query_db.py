import sqlite3
conn = sqlite3.connect(r'C:\Users\user\Desktop\hermes_claude\data\trades\paper_trades.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print('=== TABLES ===')
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print([r[0] for r in cur.fetchall()])

print()
print('=== stats_cache ALL ROWS ===')
cur.execute('SELECT * FROM stats_cache')
rows = cur.fetchall()
for r in rows:
    print(dict(r))
if not rows:
    print('(empty)')

print()
print('=== stats_cache WHERE win_rate > 1.0 ===')
cur.execute('SELECT * FROM stats_cache WHERE win_rate > 1.0')
bad_rows = cur.fetchall()
for r in bad_rows:
    print('BAD ROW:', dict(r))
if not bad_rows:
    print('(none - win_rate is clean 0-1 scale)')

print()
print('=== positions summary (closed) ===')
cur.execute("SELECT COUNT(*) as total, SUM(CASE WHEN pnl_r > 0 THEN 1 ELSE 0 END) as wins FROM positions WHERE status='closed'")
row = cur.fetchone()
print(dict(row))

print()
print('=== all positions (last 10 closed) ===')
cur.execute("SELECT id, direction, entry_price, close_price, pnl_r, status FROM positions ORDER BY close_time DESC LIMIT 10")
for r in cur.fetchall():
    print(dict(r))

conn.close()
