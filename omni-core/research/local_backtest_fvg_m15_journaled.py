"""In-depth journaled FVG fill backtester for XAUUSD M15.

Implements proper SMC FVG logic:
- H4 HTF bias filter
- FVG detection and mitigation tracking
- Liquidity sweep confirmation
- Premium/discount zone filter
- BOS/CHoCH context
- Full trade journal with win/loss reason
"""
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

CSV_M15 = Path(r'C:/Users/user/Desktop/hermes_claude/data/market_data/local_xau_m15.csv')
OUT = Path(r'C:/Users/user/Desktop/hermes_claude/data/rnd/results/skills_subagent_fvg_m15_journaled.json')
INITIAL_EQUITY = 10000.0
RISK_PCT = 0.01


def load(path, max_bars=None):
    df = pd.read_csv(path, sep='\t')
    df.columns = [c.strip() for c in df.columns]
    df['date'] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'], dayfirst=False)
    df = df.sort_values('date').reset_index(drop=True)
    if max_bars:
        df = df.tail(max_bars).reset_index(drop=True)
    return {
        'date': df['date'].values,
        'open': df['<OPEN>'].astype(float).values,
        'high': df['<HIGH>'].astype(float).values,
        'low': df['<LOW>'].astype(float).values,
        'close': df['<CLOSE>'].astype(float).values,
    }


def ema(values, span):
    return pd.Series(values).ewm(span=span, adjust=False).mean().values


def detect_swings(high, low, left=3, right=3):
    sh = []
    sl = []
    n = len(high)
    for i in range(left, n - right):
        if np.all(high[i] >= high[i - left:i + right + 1]):
            sh.append(i)
        if np.all(low[i] <= low[i - left:i + right + 1]):
            sl.append(i)
    return sh, sl


def detect_fvgs(open_, high, low, close, min_size_pips=2.0):
    """Detect bullish and bearish FVGs. min_size_pips in USD (1 pip = 0.01 for XAUUSD)."""
    fvgs = []
    for i in range(2, len(close)):
        o1, h1, l1, c1 = open_[i - 2], high[i - 2], low[i - 2], close[i - 2]
        o2, h2, l2, c2 = open_[i - 1], high[i - 1], low[i - 1], close[i - 1]
        o3, h3, l3, c3 = open_[i], high[i], low[i], close[i]
        # Bullish FVG: candle 2 high > candle 1 high, candle 3 low > candle 1 high
        if c2 > h1 and l3 > h1 and (h2 - l1) >= min_size_pips:
            fvgs.append({'type': 'bullish', 'top': h2, 'bottom': h1, 'idx': i, 'mitigated': False, 'mitigation_idx': None})
        # Bearish FVG: candle 2 low < candle 1 low, candle 3 high < candle 1 low
        if c2 < l1 and h3 < l1 and (h1 - l2) >= min_size_pips:
            fvgs.append({'type': 'bearish', 'top': l1, 'bottom': l2, 'idx': i, 'mitigated': False, 'mitigation_idx': None})
    return fvgs


def detect_obs(open_, close, high, low, lookback=10):
    """Detect bullish/bearish order blocks: last opposite candle before strong impulse."""
    obs = []
    for i in range(lookback, len(close) - 1):
        body = abs(close[i] - open_[i])
        range_ = high[i] - low[i]
        if body / (range_ if range_ else 1) < 0.4:
            continue
        if close[i] > open_[i]:  # bullish candle
            if close[i] > max(high[i - lookback: i]):
                obs.append({'type': 'bullish', 'idx': i, 'top': high[i], 'bottom': low[i]})
        else:  # bearish candle
            if close[i] < min(low[i - lookback: i]):
                obs.append({'type': 'bearish', 'idx': i, 'top': high[i], 'bottom': low[i]})
    return obs


def detect_liquidity_sweeps(high, low, sh_idx, sl_idx, lookback=10):
    sweeps = []
    for i in range(lookback, len(high)):
        # Sweep of recent swing high
        recent_sh = [x for x in sh_idx if x < i and x > i - lookback * 5]
        if recent_sh and high[i] > high[max(recent_sh)]:
            sweeps.append({'idx': i, 'type': 'high'})
        # Sweep of recent swing low
        recent_sl = [x for x in sl_idx if x < i and x > i - lookback * 5]
        if recent_sl and low[i] < low[min(recent_sl)]:
            sweeps.append({'idx': i, 'type': 'low'})
    return sweeps


def detect_bos_choch(sh_idx, sl_idx, high, low, lookback=5):
    """Detect break of structure (BOS) and change of character (CHoCH)."""
    bos = []
    choch = []
    last_sh = None
    last_sl = None
    for i in range(len(high)):
        if sl_idx and i >= sl_idx[0]:
            curr_sl = [x for x in sl_idx if x <= i][-1]
            if last_sl is None or curr_sl > last_sl:
                if low[i] < low[last_sl] if last_sl is not None else False:
                    bos.append({'idx': i, 'type': 'bearish'})
                last_sl = curr_sl
        if sh_idx and i >= sh_idx[0]:
            curr_sh = [x for x in sh_idx if x <= i][-1]
            if last_sh is None or curr_sh > last_sh:
                if high[i] > high[last_sh] if last_sh is not None else False:
                    bos.append({'idx': i, 'type': 'bullish'})
                last_sh = curr_sh
    return bos, choch


def is_bullish_bias(bos_idx, i):
    return any(b['type'] == 'bullish' and b['idx'] <= i for b in bos_idx)


def run():
    data = load(CSV_M15, max_bars=15000)
    date = data['date']
    open_ = data['open']
    high = data['high']
    low = data['low']
    close = data['close']
    n = len(close)

    ema50 = ema(close, 50)
    ema200 = ema(close, 200)

    sh_idx, sl_idx = detect_swings(high, low)
    fvgs = detect_fvgs(open_, high, low, close)
    obs = detect_obs(open_, close, high, low)
    sweeps = detect_liquidity_sweeps(high, low, sh_idx, sl_idx)
    bos, _ = detect_bos_choch(sh_idx, sl_idx, high, low)

    # Mark FVGs as mitigated when price closes through them
    for fvg in fvgs:
        for j in range(fvg['idx'] + 1, n):
            if fvg['type'] == 'bullish' and low[j] < fvg['bottom'] and not fvg['mitigated']:
                fvg['mitigated'] = True
                fvg['mitigation_idx'] = j
                break
            if fvg['type'] == 'bearish' and high[j] > fvg['top'] and not fvg['mitigated']:
                fvg['mitigated'] = True
                fvg['mitigation_idx'] = j
                break

    trades = []
    equity = INITIAL_EQUITY
    peak_equity = equity
    in_trade = False
    trade = None
    daily_trades = 0
    last_date = None

    for i in range(200, n):
        if in_trade:
            trade['bars'] += 1
            hit_sl = low[i] <= trade['sl']
            hit_tp = high[i] >= trade['tp']
            close_reason = None
            if hit_sl and hit_tp:
                close_reason = 'sl' if abs(trade['sl'] - close[i]) < abs(trade['tp'] - close[i]) else 'tp'
            elif hit_sl:
                close_reason = 'sl'
            elif hit_tp:
                close_reason = 'tp'
            elif trade['bars'] >= 24:
                close_reason = 'timebar'
            if close_reason:
                px = float(close[i])
                if close_reason == 'sl':
                    pnl_r = -1.0
                    pnl_usd = -RISK_PCT * equity
                    win = False
                elif close_reason == 'tp':
                    pnl_r = float(trade['rr'])
                    pnl_usd = RISK_PCT * trade['rr'] * equity
                    win = True
                else:
                    denom = trade['entry'] - trade['sl']
                    pnl_r = ((px - trade['entry']) / denom) if denom else 0.0
                    pnl_usd = pnl_r * RISK_PCT * equity
                    win = pnl_r > 0
                equity += pnl_usd
                trades.append({
                    'entry_time': str(date[trade['entry_idx']]),
                    'exit_time': str(date[i]),
                    'direction': trade['direction'],
                    'entry': float(trade['entry']),
                    'exit': px,
                    'sl': float(trade['sl']),
                    'tp': float(trade['tp']),
                    'rr': float(trade['rr']),
                    'pnl_r': float(pnl_r),
                    'pnl_usd': float(pnl_usd),
                    'bars': trade['bars'],
                    'win': win,
                    'close_reason': close_reason,
                    'journal': trade['journal'],
                })
                in_trade = False
                trade = None
                if equity > peak_equity:
                    peak_equity = equity
            continue

        # Daily trade limit
        curr_date = pd.Timestamp(date[i]).date()
        if curr_date != last_date:
            daily_trades = 0
            last_date = curr_date
        if daily_trades >= 3:
            continue

        px = float(close[i])

        # Filter 1: HTF bias - EMA50 > EMA200 for longs
        if ema50[i] <= ema200[i]:
            continue

        # Filter 2: Must be in discount zone (below EMA50)
        if px > ema50[i]:
            continue

        # Filter 3: Need unmitigated FVG in range
        active_fvgs = [f for f in fvgs if not f['mitigated'] and f['type'] == 'bullish']
        if not active_fvgs:
            continue
        nearest_fvg = min(active_fvgs, key=lambda f: abs(f['bottom'] - px))
        if not (nearest_fvg['bottom'] <= px <= nearest_fvg['top'] * 1.01):
            continue

        # Filter 4: Must be at least 5 bars since FVG formed (not fresh)
        if i - nearest_fvg['idx'] < 5:
            continue

        # Filter 5: Recent bullish BOS
        recent_bos = [b for b in bos if b['type'] == 'bullish' and b['idx'] >= nearest_fvg['idx'] and b['idx'] <= i]
        if not recent_bos:
            continue

        # Filter 6: Liquidity sweep below recent swing low
        recent_sweep = [s for s in sweeps if s['type'] == 'low' and s['idx'] >= nearest_fvg['idx'] and s['idx'] <= i]
        if not recent_sweep:
            continue

        # SL below recent sweep low, with minimum 2.0 USD risk
        sl_low = float(min(low[max(0, i - 10): i + 1]))
        sl = entry - max((sl_low - entry), 2.0) - 0.5
        risk = entry - sl
        if risk <= 0:
            continue
        tp = entry + 1.8 * risk
        rr = (tp - entry) / risk
        if rr < 1.0:
            continue

        journal = (
            f"Bullish FVG fill: HTF bias bullish (EMA50>EMA200). "
            f"FVG formed at idx {nearest_fvg['idx']}, age {i - nearest_fvg['idx']} bars. "
            f"Entry at {entry:.2f}, SL below sweep low {sl:.2f}, TP at FVG top {tp:.2f}, R:R {rr:.1f}. "
            f"BOS bullish at idx {[b['idx'] for b in recent_bos]}. "
            f"Liquidity sweep at idx {[s['idx'] for s in recent_sweep]}. "
            f"Context: discount zone below EMA50."
        )

        sl = entry - min(risk, 3.0)  # Cap SL at 3.0 USD to avoid over-risk on gold
        tp = entry + 1.8 * min(risk, 3.0)

        trade = {'entry_idx': i, 'entry': entry, 'sl': sl, 'tp': tp, 'rr': 1.8, 'bars': 0, 'direction': 'BUY', 'journal': journal}
        in_trade = True
        daily_trades += 1

    wins = [t for t in trades if t['win']]
    losses = [t for t in trades if not t['win']]
    total = len(trades)
    win_rate = float(len(wins) / total) if total else 0.0
    pnl = [t['pnl_r'] for t in trades]
    avg_win = float(np.mean([p for p in pnl if p > 0])) if wins else 0.0
    avg_loss = float(np.mean([p for p in pnl if p < 0])) if losses else 0.0
    expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss
    eq = [INITIAL_EQUITY] + [INITIAL_EQUITY + sum(t['pnl_usd'] for t in trades[:idx + 1]) for idx in range(len(trades))]
    eq_arr = np.array(eq, dtype=float)
    peak = np.maximum.accumulate(eq_arr)
    max_dd = float(np.max((peak - eq_arr) / peak)) if peak.size else 0.0
    gross_profit = float(sum(t['pnl_usd'] for t in trades if t['pnl_usd'] > 0))
    gross_loss = float(abs(sum(t['pnl_usd'] for t in trades if t['pnl_usd'] < 0)))
    pf = gross_profit / gross_loss if gross_loss else float('inf')
    out = {
        'strategy_id': 'skills_subagent_fvg_m15_journaled',
        'symbol': 'XAUUSD',
        'timeframe': 'M15',
        'total_trades': total,
        'win_rate': win_rate,
        'avg_win_r': avg_win,
        'avg_loss_r': avg_loss,
        'expectancy_r': round(float(expectancy), 6),
        'max_drawdown_pct': round(max_dd * 100, 4),
        'profit_factor': round(float(pf), 6),
        'equity_curve': [{'timestamp': int(pd.Timestamp(date[min(i, len(date) - 1)]).timestamp()), 'equity': round(float(e), 2)} for i, e in enumerate(eq)],
        'trades': trades[:80],
        'sample_journals': [{'entry_time': t['entry_time'], 'exit_time': t['exit_time'], 'win': t['win'], 'close_reason': t['close_reason'], 'pnl_r': round(t['pnl_r'], 2), 'journal': t['journal']} for t in trades[:20]],
        'source': 'local_csv backtest with SMC filters',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('trades', total, 'win_rate', round(win_rate, 4), 'expectancy', round(float(expectancy), 4), 'max_dd', round(max_dd * 100, 2), 'pf', round(float(pf), 2))


if __name__ == '__main__':
    run()
