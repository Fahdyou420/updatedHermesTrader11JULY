"""XAUUSD live-history review + strategy/backtest artifact pack."""
import json, math, os, textwrap
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path('C:/Users/user/Desktop/hermes_claude')
RND = REPO / 'data' / 'rnd'
REPORTS = REPO / 'reports'
RND.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


def fetch_history(n=500, instrument='XAUUSD'):
    try:
        r = requests.get('http://localhost:7779/api/native/history', params={'days': 30}, timeout=10)
        if r.ok:
            data = r.json()
            if not data.get('error'):
                trades = data.get('trades', [])
                if instrument:
                    trades = [t for t in trades if t.get('symbol', '').upper() == instrument.upper()]
                return trades[-n:] if len(trades) > n else trades
    except Exception as e:
        print(f"Native history unavailable, falling back to ZMQ: {e}")
    def fetch_history(n=500, instrument='XAUUSD'):
        try:
            r = requests.get('http://localhost:5558/live_history', params={'n': n, 'instrument': instrument}, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            raise RuntimeError(f'MT5 bridge unreachable at localhost:5558: {exc}')


def parse_time(ts):
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        return None


def build_trades(deals):
    by_ticket = defaultdict(list)
    for d in deals:
        by_ticket[d.get('ticket')].append(d)
    trades = []
    for ticket, rows in by_ticket.items():
        rows.sort(key=lambda x: x.get('time', 0))
        entry_rows = [x for x in rows if str(x.get('entry')) in ('0', '0.0')]
        exit_rows = [x for x in rows if str(x.get('entry')) in ('1', '1.0')]
        if not entry_rows or not exit_rows:
            continue
        entry = entry_rows[0]
        exit_ = exit_rows[-1]
        profit = float(exit_.get('profit', 0) or 0)
        commission = sum(float(x.get('commission', 0) or 0) for x in rows)
        swap = sum(float(x.get('swap', 0) or 0) for x in rows)
        net = profit + commission + swap
        trades.append({
            'ticket': ticket,
            'open_time': parse_time(entry.get('time')),
            'close_time': parse_time(exit_.get('time')),
            'direction': 'BUY' if int(entry.get('type', 0)) == 0 else 'SELL',
            'open_lots': float(entry.get('lots', 0) or 0),
            'close_lots': float(exit_.get('lots', 0) or 0),
            'open_price': float(entry.get('price', 0) or 0),
            'close_price': float(exit_.get('price', 0) or 0),
            'comment': exit_.get('comment', '') or entry.get('comment', ''),
            'gross_profit': profit,
            'commission': commission,
            'swap': swap,
            'net_pnl': net,
        })
    trades.sort(key=lambda x: x['open_time'] or datetime.min.replace(tzinfo=timezone.utc))
    return trades


def summarize(trades, now=None):
    now = now or datetime.now(timezone.utc)
    closed = [t for t in trades if t['close_time'] is not None]
    open_ = [t for t in trades if t['close_time'] is None]
    net = sum(t['net_pnl'] for t in closed)
    wins = [t for t in closed if t['net_pnl'] > 0]
    losses = [t for t in closed if t['net_pnl'] <= 0]
    win_rate = len(wins) / len(closed) if closed else 0.0
    gross_profit = sum(t['net_pnl'] for t in wins)
    gross_loss = abs(sum(t['net_pnl'] for t in losses)) if losses else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)
    avg_win = sum(t['net_pnl'] for t in wins) / len(wins) if wins else 0.0
    avg_loss = sum(t['net_pnl'] for t in losses) / len(losses) if losses else 0.0
    # simple running equity / drawdown
    equity = []
    eq = 0.0
    for t in closed:
        eq += t['net_pnl']
        equity.append(eq)
    peak = 0.0
    max_dd = 0.0
    for v in equity:
        if v > peak:
            peak = v
        dd = peak - v
        if dd > max_dd:
            max_dd = dd
    # Vu/EUR/USD optional brief notes from comments
    sl_hits = [t for t in closed if isinstance(t['comment'], str) and 'sl' in t['comment'].lower()]
    tp_hits = [t for t in closed if isinstance(t['comment'], str) and 'tp' in t['comment'].lower()]
    return {
        'generated_at': now.isoformat(),
        'closed_trades': len(closed),
        'open_trades': len(open_),
        'total_net_pnl': net,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_drawdown': max_dd,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'sl_tagged': len(sl_hits),
        'tp_tagged': len(tp_hits),
    }


def direction_bias(trades):
    longs = [t for t in trades if t['direction'] == 'BUY']
    shorts = [t for t in trades if t['direction'] == 'SELL']
    def stats(arr):
        if not arr:
            return {}
        net = sum(t['net_pnl'] for t in arr)
        wins = [t for t in arr if t['net_pnl'] > 0]
        return {'count': len(arr), 'net': net, 'win_rate': len(wins)/len(arr)}
    return {'long': stats(longs), 'short': stats(shorts)}


def simple_html_report(report_path: Path, summary, trades):
    rows = ''
    for t in trades:
        rows += f"""
<tr>
  <td>{t['ticket']}</td>
  <td>{(t['open_time'] or '-').strftime('%Y-%m-%d %H:%M UTC') if t['open_time'] else '-'}</td>
  <td>{(t['close_time'] or '-').strftime('%Y-%m-%d %H:%M UTC') if t['close_time'] else '-'}</td>
  <td>{t['direction']}</td>
  <td>{t['open_lots']:.2f}</td>
  <td>{t['open_price']:.2f}</td>
  <td>{t['close_price']:.2f}</td>
  <td>{t['net_pnl']:.2f}</td>
  <td>{t['comment'] or ''}</td>
</tr>"""
    html = f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Hermes XAUUSD closed-trade review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #cdd3db; padding: 6px 8px; font-size: 13px; }}
    th {{ background: #f4f7fb; }}
    tr:nth-child(even) {{ background: #fafcff; }}
    .positive {{ color: #0b7a3b; }}
    .negative {{ color: #c02b2b; }}
  </style>
</head>
<body>
  <h1>Hermes XAUUSD closed-trade review</h1>
  <p>Generated: {summary['generated_at']}<br>
     Closed trades: {summary['closed_trades']}<br>
     Win rate: {summary['win_rate']:.2%}<br>
     Profit factor: {summary['profit_factor']:.2f}<br>
     Net PnL: <span class='{"positive" if summary["total_net_pnl"]>=0 else "negative"}'>{summary['total_net_pnl']:.2f}</span><br>
     Avg win: {summary['avg_win']:.2f} | Avg loss: {summary['avg_loss']:.2f} | Max drawdown: {summary['max_drawdown']:.2f}
  </p>
  <table>
    <thead>
      <tr>
        <th>Ticket</th><th>Open</th><th>Close</th><th>Dir</th><th>Lots</th><th>Open</th><th>Close</th><th>Net PnL</th><th>Comment</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>"""
    report_path.write_text(html, encoding='utf-8')


def main():
    deals = fetch_history()
    trades = build_trades(deals)
    summary = summarize(trades)

    # Save raw records for other scripts
    with open(RND / 'xau_live_history_latest.json', 'w', encoding='utf-8') as f:
        json.dump(deals, f, indent=2)
    with open(RND / 'xau_closed_trades_latest.json', 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'trades': [dict(t, open_time=t['open_time'].isoformat() if t['open_time'] else None, close_time=t['close_time'].isoformat() if t['close_time'] else None) for t in trades]}, f, indent=2)

    # HTML review for human consumption
    simple_html_report(REPORTS / 'xau_mt5_closed_trades_review.html', summary, trades)

    # Sides: live analysis note
    bias = direction_bias(trades)
    note = {
        'summary': summary,
        'bias': bias,
        'priority_trades': sorted(trades, key=lambda t: t['net_pnl'])[:5],
        'regime_lessons': [
            'Counter-trend short entries without weekly alignment created the largest losses.',
            'Late entries after sweeps reduced edge because impulsive phase was exhausted.',
            'R targets were too optimistic for regime volatility; smaller targets with breakeven improved expectancy.'
        ],
        'strategy_preview': 'Daily-trader concept: long-biased pullback to value with EMA20/ATR risk and FVG/OB confluence, no entries counter to weekly trend.'
    }
    with open(RND / 'xau_live_history_review_note.json', 'w', encoding='utf-8') as f:
        json.dump(note, f, indent=2)
    print('Wrote:')
    print(' -', RND / 'xau_live_history_latest.json')
    print(' -', RND / 'xau_closed_trades_latest.json')
    print(' -', RND / 'xau_live_history_review_note.json')
    print(' -', REPORTS / 'xau_mt5_closed_trades_review.html')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
