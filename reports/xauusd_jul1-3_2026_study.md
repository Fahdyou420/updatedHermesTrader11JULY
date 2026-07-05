# XAUUSD Jul 1-3 2026 Multi-TF Study — Hermes Analysis
Generated: 2026-07-05
Source: local `data/market_data/live_feed.jsonl` filtered Jul 1 00:00 UTC → Jul 3 19:59 UTC

---

## 1) Coverage
- M15: 16,023 bars (2026-07-01 01:00 → 2026-07-03 19:45)
- H1: 3,486 bars (2026-07-01 01:00 → 2026-07-03 19:00)
- H4: 914 bars (2026-07-01 00:00 → 2026-07-03 16:00)
- D1: 159 bars (2026-07-01 00:00 → 2026-07-03 00:00)

## 2) Session Behavior (H1 bars)
- Asian: 1,188 bars | avg change +0.73 | avg range 17.09 | net +2.51
- London: 810 bars | avg change +0.29 | avg range 13.22 | net -0.90
- NY: 797 bars | avg change +10.79 | avg range 26.02 | net +2.56
- Overnight1: 691 bars | avg change -2.58 | avg range 17.95 | net -19.16

**Interpretation:** biggest expansion + advance in NY. London mean-change near flat, spreads tightest. Overnight gives mean-reversion dips before NY ramp.

## 3) Trend Bias
- D1 slope last10 closes: +1.5769 (upward)
- H4 slope last10 closes: +13.6952 (strong upward)
- H1 slope last10 closes: -1.1085 (short-term pullback/consolidation inside uptrend)
- D1 ATR last: 131.07
- H4 ATR last: 41.79
- H1 ATR last: 15.42
- M15 ATR last: 5.74

**Bias:** Bullish H4/D1, but H1 shows pullback digestion into premium. Not a reversal context until < 4155 closes.

## 4) Key Structure & Levels

### Jul 1-3 H4 Path
- 07-01 00:00 O 4013.93 H 4018.08 L 3992.98 C 3996.53
- 07-01 12:00 → 4115.58 impulsive move
- 07-02 16:00 → 4143.66 expansion
- 07-03 04:00 → 4195.19 local high

### Liquidity Clusters (>2 touches on 10pt grid)
- 3960: multiple swing lows
- 4060: high-density zone
- 4070, 4080: stacked liquidity
- 4120, 4130, 4140: prior-day trapped lows/swings
- 4160: active near-term support
- 4170: premium pivot
- 4180: resistance cluster
- 4190, 4195: structural highs

## 5) Trade Setup Hypotheses

### H1 / M15 Day-Trade Setups
1) Bullish OB/FVG Fill Long
- Bias: pullback into 4160-4170 zone
- Entry: 4165-4170
- SL: 4155
- TP1: 4185 (1.5R)
- TP2: 4195 (2.5R) → move SL to 4175 after TP1
- R:R baseline ~2.8:1

2) Liquidity Sweep Reversal Long
- Trigger: sweep below 4161.5 then reclaim
- Entry: 4163-4167
- SL: 4155
- TP1: 4180
- TP2: 4195
- R:R ~3.3:1

3) Breakout Continuation Long
- Trigger: H1 close > 4195 with volume/range expansion
- Entry: 4198-4202
- SL: 4185
- TP1: 4215
- TP2: 4230
- R:R ~2.0:1+

4) Short at Premium Rejection
- Trigger: M15 wick/rejection at 4185-4195 with FVG above
- Entry: 4185-4190
- SL: 4198
- TP1: 4165
- TP2: 4155
- R:R ~1.8:1

## 6) Next-Week Levels
- **Key support:** 4160, 4155 (invalidator), 4140, 4130, 4121
- **Key resistance:** 4180, 4190, 4195, 4200, 4210
- **Weekly pivot:** 4170
- If Monday holds 4160+ with reclaim, target 4195-4215.
- If breaks 4155, next demand zone 4130-4140.
- Break above 4195 invalidates short bias.

## 7) Chart Objects Sent To MT5
Sent via `POST http://localhost:5562/draw`:
- Hlines: 4195, 4190, 4180, 4170, 4160, 4140, 4121, 4090, 3960, 4060
- Zones: FVG_PREMARKET_4120_4180, JUL_RANGE_3960_4195, bias label “BULLISH H4/D1, NEUTRAL H1 PULLBACK”

## 8) System State
- Docker containers: 13/13 up including mt5_bridge, preprocessor, backtester, paper_trader, mcp_bridge, dashboard
- MT5 EA heartbeat offline: `ea_connected: false`
- MT5 bridge reachable on localhost:5558
- Paper trader reachable on localhost:5561
- Backtester reachable on localhost:5560
- Redis connected
- EA listener ports: 5562 signed from mcp_bridge; ZMQ draw path: localhost:5566; Redis host:6379

## 9) Paper Trade Queue
Queued via `POST http://localhost:5561/signal`:
- Long OB/FVG setup
- Short premium rejection setup
- Breakout continuation setup
