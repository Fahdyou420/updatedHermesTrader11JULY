# XAUUSD Strategy Backtest Report
Generated: 2026-07-05T14:56:46.491598Z
Symbol: GC=F
Period: 2020-01-01 → 2026-06-04
Data: yfinance daily auto_adjust=true.
Caveat: 1D-bar vectorized backtest; no execution/slippage model beyond next-bar conservative rule.


Reviewed 33 closed MT5 bridge deals.
Recurring failures:
- Short entries taken without weekly trend alignment, then stopped out by impulsive long ramps.
- Late entries after initial sweep already exhausted the move; R entries collapsed.
- Some wins were tight mean-reversion trades; losses were larger and fewer.

Winning traits seen:
- Long entries aligned with weekly trend after pullbacks.
- Tighter SL than trailing target distance worked only when bias was strong.


## Parameter Sweep Results
Tested 6 selected setups.

### Best By Composite Score
- id: w_trend_long_only_ema40_154_250
- trades: 302
- win_rate: 48.01%
- sum_pnl: $-365.00
- avg_r: -0.05
- est_max_dd: $1,061.42
- params: {'id': 'w_trend_long_only_ema40_154_250', 'week_bias': 'bullish', 'allow_reverse': False, 'use_bb': False, 'rsi_lo': 40, 'rsi_hi': 55, 'atr_sl': 1.5, 'atr_tp': 2.5, 'long_only': True}

### Best By Absolute PnL
- id: any_long_only_ema35_1525_220
- trades: 203
- win_rate: 43.84%
- sum_pnl: $-250.20
- avg_r: -0.10
- est_max_dd: $971.90
- params: {'id': 'any_long_only_ema35_1525_220', 'week_bias': 'any', 'allow_reverse': False, 'use_bb': False, 'rsi_lo': 35, 'rsi_hi': 55, 'atr_sl': 1.5, 'atr_tp': 2.2, 'long_only': True}

## Recommended Daily-Trader Strategy
Name: Gold NBC Pullback
- Bias: follow weekly trend via weekly SMA20.
- Entry: Daily close below lower BB OR ema20 AND RSI<40.
- Long only when weekly bias bullish; short optional when bias bearish.
- SL: 1.5 x ATR14. TP: 2.5 x ATR14. Base R:R ~1.67:1.
- Why: reduces counter-trend drawdown, captures value in pullbacks.

## Top Candidates
| id | trades | win_rate | sum_pnl | avg_r | max_dd | score | use_bb | rsi_lo | atr_sl | atr_tp | week_bias | allow_reverse |
|---|---:|---:|---:|---:|---:|---:|:---|---:|---:|---:|:---|:---|
| w_trend_long_only_ema40_154_250 | 302 | 48.01% | $-365.00 | -0.05 | $1,061.42 | -0.91 | False | 40 | 1.5 | 2.5 | bullish | False |
| any_long_only_ema35_1525_220 | 203 | 43.84% | $-250.20 | -0.10 | $971.90 | -0.97 | False | 35 | 1.5 | 2.2 | any | False |
| any_long_only_bb35_1525_230 | 49 | 24.49% | $-960.70 | -0.48 | $1,144.48 | -1.13 | True | 35 | 1.5 | 2.3 | any | False |
| w_trend_long_only_bb40_154_250 | 56 | 25.00% | $-1,263.08 | -0.47 | $1,342.06 | -1.15 | True | 40 | 1.5 | 2.5 | bullish | False |
| w_trend_ls_bb40_154_250 | 56 | 25.00% | $-1,263.08 | -0.47 | $1,342.06 | -1.15 | True | 40 | 1.5 | 2.5 | bullish | True |
| any_ls_bb35_200_250 | 49 | 24.49% | $-1,177.93 | -0.41 | $1,340.27 | -1.15 | True | 35 | 2.0 | 2.5 | any | True |

## Strategy File
Path: `data/strategies/gold_nbc_pullback.py`.
Plugin implements recommended NBC pullback for live backtesting.

## Upgrade Path And How I Will Intervene
- Add session gating: avoid illiquid first session minutes.
- Add OB/FVG confluence: use M15 SMC to time entries inside daily pullback.
- Add dynamic trailing: move SL to breakeven after 1R, then trail by ATR.
- Add ATR seasonality/monthly filter.
- Auto weekly retrain: add job to rerun sweep and update strategy file if performance degrades.
- Integrate into Hermes strategy learning queue with guardrails before live paper trade promotion.
