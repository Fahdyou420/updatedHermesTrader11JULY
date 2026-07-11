import requests, sqlite3, json, time

NATIVE = 'http://localhost:7779/api/native/latest_bars?instrument=XAUUSD&tf=M15&n=1'
DB = r'C:\Users\user\Desktop\hermes_claude\data\trades\paper_trades.db'
PID = 'pos_qa_probe'

bars = requests.get(NATIVE, timeout=10).json()
close = float(bars[0]['close'])
entry = close - 2.5
sl = entry - 0.5
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute("DELETE FROM positions WHERE id=?", (PID,))
conn.commit()
conn.execute("""
INSERT INTO positions(id,instrument,direction,entry_price,sl,tp,lots,strategy_id,setup_type,session,open_time,status,close_price,close_time,pnl_r,close_reason)
VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
""", (PID, 'XAUUSD', 'buy', entry, sl, sl+6.0, 0.01, 'qa', 'probe', 'qa', int(time.time()), 'open', 0.0, 0, 0.0, ''))
conn.commit()
row = conn.execute("SELECT entry_price,sl FROM positions WHERE id=?", (PID,)).fetchone()
risk = float(row['entry_price']) - float(row['sl'])
pnl_r = (close - entry) / risk if risk > 0 else 0.0
print(json.dumps({
    'close': close,
    'entry': entry,
    'risk': risk,
    'pnl_r': round(pnl_r, 6),
    'pnl_r_nonzero': pnl_r != 0.0
}, indent=2))
conn.close()
