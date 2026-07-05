CONFIG = dict(
    strategy_name='gold_nbc_pullback_v2',
    instrument='XAUUSD',
    base_lot=0.01,
    sl_atr_mult=1.0,
    tp_atr_mult=2.0,
    weekly_bias_required=True,
    confluence='OB/FVG/atr-volume-expansion',
)