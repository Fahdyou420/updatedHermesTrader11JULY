"""Local direct backtest runner, no services/MCP required."""
import sys
import json
import glob
import os
print('starting local_backtest_runner')

# Ensure repo is on path so we can import from ./services/...
repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print('repo', repo)
if repo not in sys.path:
    sys.path.insert(0, repo)

from services.shared.models import StrategyConfig  # noqa: E402
from services.backtester.engine import BacktestEngine  # noqa: E402

search_path = os.path.join(repo, 'data', 'market_data')
if not os.path.exists(search_path):
    raise SystemExit(f'missing data dir: {search_path}')

for path in sorted(glob.glob(os.path.join(search_path, '*M15*.json'))):
    print('candidate', path)


def load_bars(instrument: str, timeframe: str, n: int = 1000):
    cols=[]
    pattern=os.path.join(search_path, f'{instrument.upper()}_{timeframe.upper()}_*.json')
    for fp in sorted(glob.glob(pattern)):
        try:
            with open(fp,'r',encoding='utf-8') as f:
                data=json.load(f)
            if isinstance(data,list):
                cols.extend(data)
        except Exception as e:
            print('read error',fp,e)
    cols=sorted(cols, key=lambda x:x.get('timestamp',0))
    if not cols and os.path.exists(os.path.join(search_path,'live_feed.jsonl')):
        with open(os.path.join(search_path,'live_feed.jsonl'),'r',encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:b=json.loads(line)
                except: continue
                if b.get('instrument','').upper()==instrument.upper() and b.get('timeframe',b.get('tf','')).replace('PERIOD_','').upper()==timeframe.upper():
                    cols.append(b)
        cols=sorted(cols, key=lambda x:x.get('timestamp',0))
    if n:
        cols=cols[-n:]
    return cols

print('loaded bars', len(load_bars('BTCUSD','M15',500)))

cfg=StrategyConfig(
    strategy_id='local_check',
    name='Local check',
    instrument='BTCUSD',
    timeframe='M15',
    session_filter=['london','newyork','overlap'],
    entry_logic={'type':'fvg_fill','description':'local'},
    sl_logic={'type':'atr','value':15,'multiplier':1.5},
    tp_logic={'type':'atr','value':30,'multiplier':3.0},
    risk_pct=1.0,
    max_trades_per_day=1,
    spread_gate_pips=25,
    date_from='',
    date_to='',
)
bars=load_bars('BTCUSD','M15',1000)
print('actual bars', len(bars))
engine=BacktestEngine(cfg)
res=engine.run(bars)
print('trades', res.total_trades, 'win_rate', res.win_rate, 'pf', res.profit_factor)
print('first trades', res.trades[:3] if hasattr(res,'trades') else None)
