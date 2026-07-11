from pathlib import Path
from pypdf import PdfReader

v = Path('/c/Users/user/AppData/Local/hermes/obsidian/04_KNOWLEDGE_BASE')
src = Path(r'C:/Users/user/Downloads/Telegram Desktop')
out_root = Path('/c/Users/user/AppData/Local/hermes/obsidian/04_RND/candidates')
out_root.mkdir(parents=True, exist_ok=True)

items = [
  {
    'id': 'C01',
    'source': 'Inducement-Trading.pdf',
    'concept': 'Inducement Sweep + Reclaim Entry',
    'instrument': 'Major FX pairs / XAUUSD / BTC',
    'timeframe': 'M5-M15 bias from H1',
    'entry': 'Enter long when price sweeps a recent inducement high and reclaims the swept high within 1-2 candles. stop above manipulation high',
    'confirmation': 'Close back above swept high; prior H1 upstructure intact.',
    'invalidation': 'Price closes back below swept high or makes a lower high after sweep.',
    'testability': 'Exact entry based on prior swing high and close; invalidation is close below that same level within N candles.'
  },
  {
    'id': 'C02',
    'source': 'Liquidity-Grab-in-Trading.pdf',
    'concept': 'Swing-High/Low Liquidity Grab Reversal',
    'instrument': 'Any liquid market; XAUUSD preferred',
    'timeframe': 'M1-M15 entries, H1 context',
    'entry': 'Enter opposite direction after price spikes beyond swing high/low and shows immediate close back inside range. stop beyond grab extreme',
    'confirmation': 'Rejection candle with close back inside range; HTF structure aligned.',
    'invalidation': 'Close beyond grab level with momentum continuation or equal range expansion.',
    'testability': 'Defined stop/entry at exact grab level with close-based confirmation.'
  },
  {
    'id': 'C03',
    'source': 'How to Trade Using Fair Value Gap in ICT Style.pdf',
    'concept': 'Unmitigated FVG Retest Entry',
    'instrument': 'XAUUSD / NQ / ES',
    'timeframe': 'M5-M15 entries, H1 bias',
    'entry': 'If price returns to untested FVG and shows a bullish engulfing/bearish engulfing at FVG edge, enter.',
    'confirmation': 'Candle closes on opposite side of FVG after touching edge.',
    'invalidation': 'Gap fully filled without reversal candle or structure breaks opposite direction.',
    'testability': 'First-touch FVG + engulfing trigger with exact stop/target.'
  },
  {
    'id': 'C04',
    'source': 'AMD PO3 Model PDF',
    'concept': 'AMD iFVG Retest Entry',
    'instrument': 'NQ/ES/GC per source; XAUUSD candidate',
    'timeframe': '5m entries with H4-D1 AMD structure',
    'entry': 'After AMD manipulation leg closes back inside accumulation zone, enter on retest of inverted FVG created during manipulation. stop at manipulation extreme',
    'confirmation': 'Price touches iFVG and shows reversal candle; manipulation high/low defines stop.',
    'invalidation': 'Price closes outside accumulation zone or retraces beyond manipulation extreme.',
    'testability': 'Exact accumulation box/manipulation leg plus FVG edge.'
  },
  {
    'id': 'C05',
    'source': 'CHOCH in ICT PDF',
    'concept': 'CHoCH Break + First Pullback Entry',
    'instrument': 'FX, gold, indices',
    'timeframe': 'M15 trigger after H4 CHoCH',
    'entry': 'Enter when price breaks prior swing high/low after a CHoCH marks directional bias change.',
    'confirmation': 'Close beyond prior broken level with momentum; previous structure shifts.',
    'invalidation': 'Price retraces and reclaims the old structure level within 2-3 candles.',
    'testability': 'Structural break + close-based pullback trigger with fixed window.'
  },
  {
    'id': 'C06',
    'source': 'Smart-Money-Concept-trading-strategy-PDF.pdf',
    'concept': 'SMC Pullback to Bullish/Bearish Order Block',
    'instrument': 'XAUUSD / EURUSD / GBPUSD',
    'timeframe': 'M15 entries, H4 structure filter',
    'entry': 'Price retests last bullish/bearish order block after BOS and enters on rejection candle. stop beyond OB',
    'confirmation': 'Pin bar/engulfing at OB zone; BOS direction matches OB side.',
    'invalidation': 'OB zone breaks with closing candle beyond OB extremes.',
    'testability': 'Exact OB zone, BOS rule, and close-based invalidation.'
  },
  {
    'id': 'C07',
    'source': '15_Scalping_Strategies.pdf',
    'concept': 'M15 EMA Ribbon Pullback Scalp',
    'instrument': 'XAUUSD / indices / major FX',
    'timeframe': 'M1-M5 entries, M15 EMA trend filter',
    'entry': 'Long if price pulls back to fast EMA from above after M15 EMA ribbon slopes up, on first close back above EMA. stop below pullback low',
    'confirmation': 'Close above rising fast EMA with higher low structure on trigger TF.',
    'invalidation': 'Close below EMA or new lower low within 2 candles.',
    'testability': 'Uses exact close vs EMA, slope rules, and 2-candle invalidation.'
  },
  {
    'id': 'C08',
    'source': '1-Minute-Scalping-Strategy.pdf',
    'concept': '1-Minute Tight Range Breakout Retest',
    'instrument': 'High-liquidity pairs / XAUUSD',
    'timeframe': '1m entries, 15m structure',
    'entry': 'Wait for 1m breakout from tight 20-candle range; enter on first pullback to breakout level. stop beyond opposite range bound',
    'confirmation': 'Breakout candle closes outside range; pullback touches breakout level.',
    'invalidation': 'Price rejects breakout level and closes beyond opposite range bound.',
    'testability': 'Exact range length and breakout/retest rule.'
  },
  {
    'id': 'C09',
    'source': 'Break_of_Market_Structure_BOS PDF',
    'concept': 'H4 BOS M15 Pullback Continuation',
    'instrument': 'Any trended market',
    'timeframe': 'M15 entries with H4 BOS trend',
    'entry': 'If H4 breaks structure, enter M15 pullback to broken S/R with engulfing. stop beyond opposite structure point',
    'confirmation': 'Close beyond prior swing point on H4; M15 pullback holds with engulfing.',
    'invalidation': 'Pullback breaks opposite side of broken zone on M15.',
    'testability': 'Levels are exact prior swing points; trigger is close-based.'
  },
  {
    'id': 'C10',
    'source': 'keys-to-trading-gold-ca.pdf',
    'concept': 'Weekly/Daily Psychological Level Rejection',
    'instrument': 'XAUUSD only',
    'timeframe': 'Daily entries, weekly levels',
    'entry': 'Enter on close rejection at weekly/daily psychological level or prior weekly high/low. stop beyond tested level',
    'confirmation': 'Rejection candle closes back from level within 1 candle; session wick confirms.',
    'invalidation': 'Daily close beyond level with follow-through next candle.',
    'testability': 'Discrete weekly/daily highs/lows with close-based rule.'
  },
  {
    'id': 'C11',
    'source': 'keys-to-trading-gold-ca.pdf',
    'concept': 'Gold Trendline + F&R Zone Confluence Entry',
    'instrument': 'XAUUSD',
    'timeframe': 'H4 entries, daily trendline',
    'entry': 'Enter when price touches rising/falling trendline and F&R zone at same level; close beyond trendline confirms entry. stop beneath trendline',
    'confirmation': 'Trendline from two swing points; F&R zone is prior tested support/resistance.',
    'invalidation': 'Price closes below trendline or zone with momentum candle >10 pips.',
    'testability': 'Exact trendline construction plus zone width makes this falsifiable.'
  },
  {
    'id': 'C12',
    'source': 'keys-to-trading-gold-ca.pdf',
    'concept': 'Gold Box Consolidation Breakout Entry',
    'instrument': 'XAUUSD',
    'timeframe': 'M15 entries within H1 box',
    'entry': 'Enter on close outside 10-20 pip box range after 10+ candles inside. stop just inside box',
    'confirmation': 'Range box defined by prior highs/lows; breakout candle closes outside box.',
    'invalidation': 'Close back inside box within 1 candle signals false breakout.',
    'testability': 'Exact box length and 1-candle invalidation rule.'
  }
]

for c in items:
    safe_name = c['concept'].replace('/', '_').replace('\\', '_').replace(':', '_')
    fname = f"{c['id']}_{'_'.join(safe_name.split()[:8])}.md"
    p = Path('/c/Users/user/Desktop/hermes_claude/data/rnd/candidates') / fname
    p.parent.mkdir(parents=True, exist_ok=True)
    text = f"""---
source: {c['source']}
instrument: {c.get('instrument', '')}
timeframe: {c.get('timeframe', '')}
status: candidate
---

# {c['concept']}

## Entry
{c.get('entry', '')}

## Confirmation
{c.get('confirmation', '')}

## Invalidation
{c.get('invalidation', '')}

## Testability note
{c.get('testability', '')}
"""
    p.write_text(text, encoding='utf-8')
    print('WROTE', p, 'exists=', p.exists())
