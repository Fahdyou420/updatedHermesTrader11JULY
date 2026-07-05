# XAUUSD Historic Trade History — From MT5 Bridge
Source: `GET http://localhost:5558/live_history?n=500&instrument=XAUUSD`
Store: in-memory live history accumulated from EA ZMQ `type=history` messages
Max cap: 500 records

## Summary
- Total records retrieved: 33
- Instruments: XAUUSD only
- Direction count: BUY=16, SELL=17
- Net PnL: -2,250.62
  - profit: sum across records
  - swap/sign included in net
  - commissions included in net
- Positive net deals: 11
- Zero/opener deals with only commission: multiple
- Worst single deal net: -4,557.07
- Best single deal net: +2,680.15

## Top 10 By Net PnL
| Time | Ticket | Side | Lots | Price | Net | Note |
|---|---|---|---|---:|---:|---|
| 2026-06-26 17:04 | 463250576 | BUY | 1.00 | 4078.55 | +2680.15 | [tp 4078.20] |
| 2026-07-03 04:12 | 467579914 | BUY | 0.30 | 4178.60 | +1594.22 | [tp 4177.90] |
| 2026-06-30 17:21 | 465348346 | BUY | 0.30 | 4054.70 | +703.25 | [tp 4054.21] |
| 2026-07-01 10:37 | 465857114 | SELL | 0.10 | 3968.29 | +606.78 | |
| 2026-07-01 10:37 | 465857116 | SELL | 0.18 | 3968.29 | +266.80 | |
| 2026-07-01 10:37 | 465857115 | SELL | 0.16 | 3968.29 | +234.76 | |
| 2026-07-01 10:37 | 465857117 | SELL | 0.22 | 3968.29 | +225.33 | |
| 2026-06-25 18:11 | 462323336 | SELL | 1.00 | 4009.96 | +206.19 | |
| 2026-07-01 10:37 | 465857118 | SELL | 0.20 | 3968.29 | +177.24 | |
| 2026-06-30 01:09 | 464672597 | SELL | 0.30 | 4021.31 | +78.24 | [sl 4021.31] |

## Bottom 10 By Net PnL
| Time | Ticket | Side | Lots | Price | Net | Note |
|---|---|---|---|---:|---:|---|
| 2026-07-02 15:30 | 467020994 | SELL | 1.00 | 4099.38 | -4557.07 | [sl 4093.00] |
| 2026-06-29 16:48 | 464296236 | BUY | 1.00 | 4033.30 | -1574.82 | [sl 4033.65] |
| 2026-07-01 16:24 | 466146378 | SELL | 0.51 | 4045.18 | -1278.48 | [sl 4045.00] |
| 2026-07-01 16:24 | 466146371 | SELL | 0.51 | 4045.18 | -1048.98 | [sl 4045.00] |
| 2026-06-29 16:37 | 464276128 | BUY | 0.40 | 4034.40 | -543.13 | [sl 4034.69] |
| 2026-06-26 12:54 | 462994990 | SELL | 1.00 | 4051.72 | -2.84 | |
| 2026-07-01 22:40 | 466529043 | BUY | 1.00 | 4054.42 | -2.84 | |
| 2026-06-29 16:08 | 464234292 | SELL | 1.00 | 4049.02 | -2.83 | |
| 2026-06-25 18:11 | 462322063 | BUY | 1.00 | 4012.05 | -2.81 | |
| 2026-07-01 15:38 | 466076087 | BUY | 0.51 | 4024.64 | -1.44 | |

## Jul 1-3 2026 Window Subset
Inside 2026-07-01 00:00 UTC → 2026-07-03 23:59 UTC:
- Notable cluster at 2026-07-01 10:37 UTC: 5 SELL orders at 3968.29
  - combined lots 0.86
  - outcomes: +606.78, +234.76, +266.80, +225.33, +177.24
- 2026-07-01 16:24 UTC: two SELL closes 4045.18 SL hits for big losses
- 2026-07-02 15:30 UTC: SELL at 4099.38 closed SL: -4557.07
- 2026-07-03 04:12 UTC: BUY TP at 4178.60: +1594.22

## Notes / Caveats
- This store is in-memory and capped; it is not a terminal-exported full statement.
- Records are deal-event snapshots, not paired positions; wins and losses need reconciliation by position_id/direction to reconstruct rounded trade outcomes.
- For a definitive broker report, use MT5 terminal account history export.
