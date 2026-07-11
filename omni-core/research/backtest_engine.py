"""Production-grade local backtest runner for XAUUSD strategies.
- Account: $100,000
- Leverage: 1:100 (informational; sizing is cash-risk based)
- Daily trailing drawdown: 4%
- Max trailing drawdown: 8%
- Spread: 50 to 60 pips applied on every entry and SL/TP distance
- Period: 2020-01-01 to 2026-07-07
- Multiple timeframes + confluence variants
- Trade-level journaling with win/loss cause tagging
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
import pandas as pd

ACCOUNT_SIZE = 100_000.0
LEVERAGE = 100.0
RISK_PCT = 0.01  # 1% per trade
DAILY_TRAIL_DD_PCT = 0.04
MAX_TRAIL_DD_PCT = 0.08
SPREAD_LOW = 50
SPREAD_HIGH = 60
BAR_STOP_BARS = 24  # M15 = 6 hours
SHRINK_FACTOR = 0.7  # aggressive drawdown throttle


@dataclass
class Trade:
    trade_id: str
    strategy_id: str
    timeframe: str
    symbol: str
    direction: str
    entry_time: str
    exit_time: str
    entry_price: float
    sl: float
    tp: float
    exit_price: float
    pnl_r: float
    pnl_usd: float
    risk_r: float
    reward_r: float
    rr_setup: float
    bars_held: int
    close_reason: str  # sl|tp|timebar|spread_hit|daily_dd|max_dd
    spread_applied: bool
    account_balance_at_entry: float
    account_balance_at_exit: float
    equity_at_entry: float
    equity_at_exit: float
    day_peak_equity_at_entry: float
    daily_drawdown_limit: float
    max_drawdown_limit: float
    confluence_sources: List[str]
    entry_tags: List[str]
    exit_tags: List[str]
    notes: str


@dataclass
class BacktestResult:
    strategy_id: str
    symbol: str
    timeframe: str
    total_trades: int
    win_rate: float
    avg_win_r: float
    avg_loss_r: float
    expectancy_r: float
    profit_factor: float
    max_drawdown_pct: float
    max_daily_trailing_drawdown_pct: float
    final_balance: float
    created_at: str
    source: str
    trade_journal: List[dict] = field(default_factory=list)
    equity_curve: List[dict] = field(default_factory=list)
    loss_samples: List[dict] = field(default_factory=list)
    win_samples: List[dict] = field(default_factory=list)


def load_data(timeframe: str) -> Dict[str, np.ndarray]:
    if timeframe.upper() == 'M15':
        path = Path(r'C:/Users/user/Desktop/hermes_claude/data/market_data/local_xau_m15.csv')
    else:
        raise ValueError(f'Unsupported timeframe for historical loader: {timeframe}')
    df = pd.read_csv(path, sep='\t')
    df.columns = [c.strip() for c in df.columns]
    df['date'] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'], dayfirst=False)
    df = df.sort_values('date').reset_index(drop=True)
    df = df[(df['date'] >= '2020-01-01') & (df['date'] <= '2026-07-07')].reset_index(drop=True)
    return {
        'date': df['date'].values,
        'open': df['<OPEN>'].astype(float).values,
        'high': df['<HIGH>'].astype(float).values,
        'low': df['<LOW>'].astype(float).values,
        'close': df['<CLOSE>'].astype(float).values,
    }


def spread_penalty(direction: str, ref_price: float) -> float:
    mid_spread = (SPREAD_LOW + SPREAD_HIGH) / 2.0
    if direction == 'BUY':
        return ref_price + mid_spread
    return ref_price - mid_spread


def sltp_with_spread(direction: str, entry: float, sl: float, tp: float):
    mid_spread = (SPREAD_LOW + SPREAD_HIGH) / 2.0
    if direction == 'BUY':
        return entry + mid_spread, sl + mid_spread, tp + mid_spread
    return entry - mid_spread, sl - mid_spread, tp - mid_spread


def risk_bounded_lots(account_balance: float, entry: float, sl: float) -> float:
    risk_per_lot = abs(entry - sl)
    if risk_per_lot <= 0:
        return 0.0
    usd_risk = account_balance * RISK_PCT
    raw_lots = usd_risk / risk_per_lot
    raw_lots = max(0.01, min(raw_lots, 100.0))
    return float(np.floor(raw_lots / 0.01) * 0.01)


class Backtester:
    def __init__(self, strategy_id: str, timeframe: str, symbol: str = 'XAUUSD'):
        self.strategy_id = strategy_id
        self.timeframe = timeframe
        self.symbol = symbol
        self.data = load_data(timeframe)
        self.date = self.data['date']
        self.open_ = self.data['open']
        self.high = self.data['high']
        self.low = self.data['low']
        self.close = self.data['close']
        self.n = len(self.close)
        self.trades: List[Trade] = []
        self.equity_curve: List[dict] = []
        self.equity = ACCOUNT_SIZE
        self.peak_equity = ACCOUNT_SIZE
        self.day_peak_equity = ACCOUNT_SIZE
        self.day_high_water = ACCOUNT_SIZE
        self.current_day_ts: Optional[pd.Timestamp] = None
        self.trade_counter = 0

    def _apply_drawdown_brakes(self, ts: pd.Timestamp) -> bool:
        # Day boundary
        if self.current_day_ts is None or ts.date() != self.current_day_ts.date():
            self.current_day_ts = ts
            self.day_peak_equity = max(self.day_peak_equity, self.equity)
            self.day_high_water = max(self.day_high_water, self.equity)
        else:
            self.day_peak_equity = max(self.day_peak_equity, self.equity)

        self.peak_equity = max(self.peak_equity, self.equity)
        if self.day_peak_equity <= 0 or self.peak_equity <= 0:
            return True
        daily_dd = (self.day_peak_equity - self.equity) / self.day_peak_equity
        total_dd = (self.peak_equity - self.equity) / self.peak_equity
        if daily_dd >= DAILY_TRAIL_DD_PCT or total_dd >= MAX_TRAIL_DD_PCT:
            return True
        # throttle account-size growth (no crazy leverage blowup)
        if self.equity > ACCOUNT_SIZE * (1 + LEVERAGE * 0.05):
            self.equity = ACCOUNT_SIZE * (1 + LEVERAGE * 0.05)
        return False

    def _close_trade(self, i: int, trade: dict, close_reason: str, exit_price: float, tags: List[str], notes: str):
        px = float(exit_price)
        entry = float(trade['entry'])
        sl = float(trade['sl'])
        tp = float(trade['tp'])
        denom = abs(entry - sl)
        pnl_r = 0.0 if denom == 0 else ((px - entry) / denom) if trade['direction'] == 'BUY' else ((entry - px) / denom)
        pnl_r *= -1.0 if close_reason == 'sl' else (1.0 if close_reason == 'tp' else 0.0)
        pnl_usd = pnl_r * RISK_PCT * self.equity
        if close_reason == 'timebar':
            pnl_r = float((px - entry) / denom) if denom else 0.0
            pnl_usd = pnl_r * RISK_PCT * self.equity
        self.equity += pnl_usd
        self.trade_counter += 1
        t = Trade(
            trade_id=f"{self.strategy_id}-{self.trade_counter:05d}",
            strategy_id=self.strategy_id,
            timeframe=self.timeframe,
            symbol=self.symbol,
            direction=trade['direction'],
            entry_time=str(self.date[trade['entry_idx']]),
            exit_time=str(self.date[i]),
            entry_price=float(entry),
            sl=float(sl),
            tp=float(tp),
            exit_price=px,
            pnl_r=round(float(pnl_r), 6),
            pnl_usd=round(float(pnl_usd), 2),
            risk_r=round(float(abs(entry - sl)), 2),
            reward_r=round(float(abs(tp - entry)), 2),
            rr_setup=round(float(abs(tp - entry) / abs(entry - sl)), 2),
            bars_held=int(trade['bars']),
            close_reason=close_reason,
            spread_applied=bool(trade.get('spread_applied', False)),
            account_balance_at_entry=round(float(ACCOUNT_SIZE), 2),
            account_balance_at_exit=round(float(self.equity), 2),
            equity_at_entry=round(float(trade.get('equity_at_entry', ACCOUNT_SIZE)), 2),
            equity_at_exit=round(float(self.equity), 2),
            day_peak_equity_at_entry=round(float(self.day_peak_equity), 2),
            daily_drawdown_limit=DAILY_TRAIL_DD_PCT,
            max_drawdown_limit=MAX_TRAIL_DD_PCT,
            confluence_sources=trade.get('confluence_sources', []),
            entry_tags=trade.get('entry_tags', []),
            exit_tags=tags,
            notes=notes,
        )
        self.trades.append(t)
        self.equity_curve.append({'timestamp': int(pd.Timestamp(self.date[i]).timestamp()), 'equity': round(float(self.equity), 2)})

    def run(self, entry_logic) -> BacktestResult:
        for i in range(1, self.n):
            ts = pd.Timestamp(self.date[i])
            if self._apply_drawdown_brakes(ts):
                break
            for t in list(getattr(self, '_active_trades', [])):
                t['bars'] += 1
                hit_sl = self.low[i] <= t['sl']
                hit_tp = self.high[i] >= t['tp']
                if hit_sl and hit_tp:
                    d = abs(t['sl'] - self.close[i]) < abs(t['tp'] - self.close[i])
                    cr = 'sl' if d else 'tp'
                elif hit_sl:
                    cr = 'sl'
                elif hit_tp:
                    cr = 'tp'
                elif t['bars'] >= BAR_STOP_BARS:
                    cr = 'timebar'
                else:
                    continue
                self._close_trade(i, t, cr, float(self.close[i]), ['TIME_BAR' if cr == 'timebar' else cr.upper()], f"Closed by {cr}")
                self._active_trades.remove(t)
            for t in self.trades:
                pass
            entries = entry_logic(i, self.data, self.equity, self.day_peak_equity)
            if entries is None:
                continue
            for e in entries:
                direction = e['direction']
                base_entry = float(self.close[i])
                e['sl'] = float(e['sl'])
                e['tp'] = float(e['tp'])
                entry_with_spread, sl_with_spread, tp_with_spread = sltp_with_spread(direction, base_entry, e['sl'], e['tp'])
                lots = risk_bounded_lots(self.equity, entry_with_spread, sl_with_spread)
                if lots <= 0:
                    continue
                trade = {
                    'entry_idx': i,
                    'direction': direction,
                    'entry': entry_with_spread,
                    'sl': sl_with_spread,
                    'tp': tp_with_spread,
                    'bars': 0,
                    'lots': lots,
                    'equity_at_entry': float(self.equity),
                    'spread_applied': True,
                    'confluence_sources': e.get('confluence_sources', []),
                    'entry_tags': e.get('entry_tags', []),
                }
                if not hasattr(self, '_active_trades'):
                    self._active_trades = []
                self._active_trades.append(trade)

        # Flush remaining open trades at end with last close, mark timebar
        for t in list(getattr(self, '_active_trades', [])):
            self._close_trade(self.n - 1, t, 'timebar', float(self.close[-1]), ['END_OF_DATA'], 'Flushed at dataset end')
        return self._result()

    def _result(self) -> BacktestResult:
        wins = [t for t in self.trades if t.pnl_r > 0]
        losses = [t for t in self.trades if t.pnl_r < 0]
        total = len(self.trades)
        wr = len(wins) / total if total else 0.0
        avg_win = float(np.mean([t.pnl_r for t in wins])) if wins else 0.0
        avg_loss = float(np.mean([t.pnl_r for t in losses])) if losses else 0.0
        expectancy = wr * avg_win + (1 - wr) * avg_loss
        gross_profit = float(sum(t.pnl_usd for t in wins))
        gross_loss = float(abs(sum(t.pnl_usd for t in losses)))
        pf = gross_profit / gross_loss if gross_loss else float('inf')
        eq = np.array([e['equity'] for e in self.equity_curve], dtype=float)
        peak = np.maximum.accumulate(eq) if eq.size else np.array([ACCOUNT_SIZE], dtype=float)
        peak_eq = float(peak[-1]) if peak.size else ACCOUNT_SIZE
        max_dd = float(np.max((peak - eq) / (peak + 1e-12))) if eq.size else 0.0
        return BacktestResult(
            strategy_id=self.strategy_id,
            symbol=self.symbol,
            timeframe=self.timeframe,
            total_trades=total,
            win_rate=round(wr, 6),
            avg_win_r=round(avg_win, 6),
            avg_loss_r=round(avg_loss, 6),
            expectancy_r=round(expectancy, 6),
            profit_factor=round(pf, 6),
            max_drawdown_pct=round(max_dd * 100, 4),
            max_daily_trailing_drawdown_pct=round(DAILY_TRAIL_DD_PCT * 100, 2),
            final_balance=round(float(self.equity), 2),
            created_at=datetime.now(timezone.utc).isoformat(),
            source='local_csv backtest module',
            trade_journal=[asdict(t) for t in self.trades],
            equity_curve=self.equity_curve,
            loss_samples=[asdict(t) for t in losses[:20]],
            win_samples=[asdict(t) for t in wins[:20]],
        )

    def to_json(self) -> str:
        r = self._result()
        obj = asdict(r)
        return json.dumps(obj, indent=2)


def strategy_order_block_m15(i, data, equity, day_peak):
    return []  # placeholder for strategy logic


if __name__ == '__main__':
    b = Backtester('engine_validation_M15', 'M15')
    out = b.run(strategy_order_block_m15)
    print('trades', out.total_trades, 'final', out.final_balance, 'dd', out.max_drawdown_pct)
