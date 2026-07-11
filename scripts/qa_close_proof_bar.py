import requests, time, json, sqlite3

NATIVE = 'http://localhost:7779/api/native/latest_bars?instrument=XAUUSD&tf=M15&n=1'
DB = r'C:\Users\user\Desktop\hermes_claude\data\trades\paper_trades.db'
PID = 'pos_qa_proof_final_v2'
CLOSE_URL = 'http://127.0.0.1:5561/close/' + PID

# Step 1: insert fake entry far from current market
bars = requests.get(NATIVE, timeout=10).json()
current_close = float(bars[0]['close'])
entry = round(current_close - 2.5, 2)  # lower than live
sl = round(entry - 0.5, 2)

# Step 2: poll until next M15 timestamp appears, then close immediately
last_ts = int(bars[0]['time'])
print('start', json.dumps({'last_ts': last_ts, 'close': current_close, 'entry': entry}))

start = time.time()
for i in range(180):
    try:
        r = requests.get(NATIVE, timeout=10).json()
        ts = int(r[0]['time'])
        if ts > last_ts:
            print(json.dumps({'event': 'BAR_ROLLED', 'i': i, 'ts': ts, 'close': r[0]['close']}))
            # close immediately using the new bar close
            close = float(r[0]['close'])
            cr = requests.post(CLOSE_URL, timeout=10)
            print('close_http', cr.status_code, cr.text[:200])
            break
        if i % 12 == 0:
            print(json.dumps({'event': 'poll', 'i': i, 'ts': ts, 'close': r[0]['close']}))
    except Exception as e:
        print(json.dumps({'event': 'err', 'i': i, 'err': str(e)}))
    time.sleep(5)
else:
    print(json.dumps({'event': 'timeout', 'elapsed': int(time.time() - start)}))

# Step 3: read DB row
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT entry_price,close_price,pnl_r,status FROM positions WHERE id=?", (PID,)).fetchone()
print('db_row', json.dumps(dict(row) if row else {'status': 'missing'}, indent=2))
