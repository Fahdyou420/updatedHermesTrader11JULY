
# strategy_name = gold_nbc_pullback_v2
# bias = weekly bullish structure, EMA20 dynamic value
# mean_reversion = weekly EMA20 slope + pullback distance <= 10% ATR14
# risk = position_size = 0.01 lot per $100 account per ATR risk unit
# sl_tp = 1x ATR14 stop, 2x ATR14 target
# confluence = prior swing OB/FVG and ATR-normalized volume expansion
# time_exit_strategy = breakeven trigger at 1R

CONFIG = dict(
    strategy_name="gold_nbc_pullback_v2",
    instrument="XAUUSD",
    base_lot=0.01,
    sl_atr_mult=1.0,
    tp_atr_mult=2.0,
    atr_lookback=14,
    ema_fast=20,
    ema_slow=None,
    weekly_bias_required=True,
)
