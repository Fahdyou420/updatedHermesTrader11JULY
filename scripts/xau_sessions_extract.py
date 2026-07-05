"""Extract XAUUSD closed trades from latest live history without exact entry flags,
using explicit close markers and symbol/time ordering."""
import json, os, math
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone

REPO = Path('C:/Users/user/Desktop/hermes_claude')
RND = REPO / 'data' / 'rnd'
RND.mkdir(exist_ok=True)


def load_deals():
    p = RND / 'xau_live_history_latest.json'
    if not p.exists():
        raise FileNotFoundError(str(p))
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_exit(d):
    c = (d.get('comment') or '')
    return 'tp' in c.lower() or 'sl' in c.lower()


def build_sessions():
    deals = load_deals()
    if not deals:
        return []
    # Normalize and sort
    deals = [d for d in deals if d.get('symbol','').upper() == 'XAUUSD']
    deals = sorted(deals, key=lambda d: (d.get('time', 0), d.get('ticket', 0)))
    exits = [d for d in deals if is_exit(d)]
    opens = [d for d in deals if not is_exit(d)]
    # For each exit, infer prior unmatched open by same direction or first unmatched open.
    used = set()
    sessions = []
    # Candidate open pool sorted by time
    opens_sorted = sorted(opens, key=lambda d: (d.get('time', 0), d.get('ticket', 0)))
    open_idx = 0
    for ex in exits:
        ex_dir = 'BUY' if int(ex.get('type', 0)) == 0 else 'SELL'
        ex_price = float(ex.get('price', 0) or 0)
        profit = float(ex.get('profit', 0) or 0)
        commission = float(ex.get('commission', 0) or 0)
        swap = float(ex.get('swap', 0) or 0)
        net = profit + commission + swap
        # find next unmatched open closest in time with matching or compatible direction
        best = None
        best_idx = None
        for i in range(open_idx, len(opens_sorted)):
            op = opens_sorted[i]
            if id(op) in used:
                continue
            op_dir = 'BUY' if int(op.get('type', 0)) == 0 else 'SELL'
            if op_dir != ex_dir:
                continue
            if best is None or abs(op.get('time', 0) - ex.get('time', 0)) < abs(best.get('time', 0) - ex.get('time', 0)):
                best = op
                best_idx = i
        if best is None:
            continue
        used.add(id(best))
        # If multiple exits share same time+ticket set, group them under one ticket if available.
        open_price = float(best.get('price', 0) or 0)
        sessions.append({
            'ticket': best.get('ticket'),
            'close_ticket': ex.get('ticket'),
            'direction': ex_dir,
            'open_time': datetime.fromtimestamp(int(best.get('time', 0)), tz=timezone.utc).isoformat() if best.get('time') else None,
            'close_time': datetime.fromtimestamp(int(ex.get('time', 0)), tz=timezone.utc).isoformat() if ex.get('time') else None,
            'open_lots': float(best.get('lots', 0) or 0),
            'close_lots': float(ex.get('lots', 0) or 0),
            'open_price': open_price,
            'close_price': ex_price,
            'gross_profit': profit,
            'commission': commission,
            'swap': swap,
            'net_pnl': net,
            'outcome': 'tp' if 'tp' in (ex.get('comment') or '').lower() else 'sl' if 'sl' in (ex.get('comment') or '').lower() else 'close',
            'comment': ex.get('comment', '') or best.get('comment', ''),
        })
        open_idx = best_idx + 1 if best_idx is not None else open_idx
    return sessions


def summary(sessions):
    closed = sessions
    net = sum(x['net_pnl'] for x in closed)
    wins = [x for x in closed if x['net_pnl'] > 0]
    losses = [x for x in closed if x['net_pnl'] <= 0]
    return {
        'sessions': len(sessions),
        'closed': len(closed),
        'total_net_pnl': net,
        'win_rate': len(wins) / len(closed) if closed else 0.0,
        'profit_factor': (sum(x['net_pnl'] for x in wins) / abs(sum(x['net_pnl'] for x in losses))) if losses and sum(x['net_pnl'] for x in losses) != 0 else float('inf'),
        'avg_win': sum(x['net_pnl'] for x in wins) / len(wins) if wins else 0.0,
        'avg_loss': sum(x['net_pnl'] for x in losses) / len(losses) if losses else 0.0,
        'max_dd_abs': 0.0,
    }


def main():
    sessions = build_sessions()
    if not sessions:
        print('NO_SESSIONS')
        raise SystemExit(1)
    s = summary(sessions)
    print(s)


if __name__ == '__main__':
    main()
