import json, datetime, math
history = json.load(open('C:/Users/user/Desktop/hermes_claude/data/rnd/xau_native_history_latest.json'))
# if total=8 but file might be stale; fallback to exact endpoint or saved temp? use exact file
trades = history['trades']
print('tickets:', len(trades))
for t in trades:
    dt = datetime.datetime.utcfromtimestamp(t['time']).isoformat()+'Z'
    print(dt, '\t', 'entry' if t['entry']==0 else 'exit', '\t', 'pos', t['position_id'], '\t', 'vol', t['volume'], '\t', 'pnl', t['profit'], '\t', 'price', t['price'], '\t', t['comment'])

pairs = {}
for t in trades:
    pos = str(t['position_id'])
    if pos not in pairs:
        pairs[pos] = {'entries':[], 'exits':[]}
    if t['entry']==0:
        pairs[pos]['entries'].append({'time':t['time'], 'price':t['price'], 'vol':t['volume']})
    else:
        pairs[pos]['exits'].append({'time':t['time'], 'price':t['price'], 'pnl':t['profit'], 'vol':t['volume'], 'reason':t['comment'], 'entry_price': next((e['price'] for e in pairs[pos]['entries']), None)})

print('positions:', len(pairs))
for pos, v in pairs.items():
    print('POS', pos, 'entries', len(v['entries']), 'exits', len(v['exits']), v)

paired = []
for pos, v in pairs.items():
    if v['entries'] and v['exits']:
        entry = v['entries'][0]
        exit = v['exits'][0]
        net = sum(x['pnl'] for x in v['exits'])
        paired.append({'position': pos, 'entry_price': entry['price'], 'exit_price': exit['price'], 'volume': entry['vol'], 'pnl': net, 'reason': exit['reason']})
print('paired count', len(paired))
net_pnl = sum(p['pnl'] for p in paired)
print('net_pnl', round(net_pnl,2))
print('wins', sum(1 for p in paired if p['pnl']>0))
print('losses', sum(1 for p in paired if p['pnl']<=0))
print('win_rate', round(sum(1 for p in paired if p['pnl']>0)/len(paired)*100,2) if paired else 0)
print('avg_win', round(sum(p['pnl'] for p in paired if p['pnl']>0)/sum(1 for p in paired if p['pnl']>0),2) if any(p['pnl']>0 for p in paired) else None)
print('avg_loss', round(sum(p['pnl'] for p in paired if p['pnl']<=0)/sum(1 for p in paired if p['pnl']<=0),2) if any(p['pnl']<=0 for p in paired) else None)
