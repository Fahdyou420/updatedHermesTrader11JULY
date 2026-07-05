# Strategy Learning Report — 2026-07-05 13:23:24+00:00

- instrument: `XAUUSD`
- timeframe: `M5`
- strategies_attempted: `7`
- baseline_results: `7`
- variant_results: `36`
- learned_strategies: `0`

## Baseline

| Strategy | Trades | Win Rate | Expectancy R | Profit Factor | Max DD | Sharpe | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00 | 0.00% | 0.00 | -1000.00 |

## Candidates

| Strategy | Trades | Win Rate | Profit Factor | Max DD | Score | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | baseline |
| `ob_reaction` | None | 0.0% | 0.00 | 0.00% | -1000.00 | baseline |
| `bos_retest` | None | 0.0% | 0.00 | 0.00% | -1000.00 | baseline |
| `choch_confirm` | None | 0.0% | 0.00 | 0.00% | -1000.00 | baseline |
| `ob_fvg_confluent` | None | 0.0% | 0.00 | 0.00% | -1000.00 | baseline |
| `liquidity_sweep_reversal` | None | 0.0% | 0.00 | 0.00% | -1000.00 | baseline |
| `killzone_ob_entry` | None | 0.0% | 0.00 | 0.00% | -1000.00 | baseline |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |
| `fvg_fill` | None | 0.0% | 0.00 | 0.00% | -1000.00 | variant |

## Saved Learned Strategies

No strategies cleared the learning bar this cycle.

## Upgrades/Observations

- Baseline execution reads every builtin/custom strategy from `list_strategies`
- Variant sweep scans ATR and fixed structure SL/TP combinations plus lookback/risk grid
- Learned scaffolds are written to `/data/strategies` and are immediately backtestable
- Reports are human-readable Markdown in `/reports` and machine-readable in this `strategy_learning.json` ledger

Generated at `2026-07-05 13:23:29+00:00`