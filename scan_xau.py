import pandas as pd
import json

def read_m15():
    df = pd.read_csv('data/market_data/local_xau_m15.csv', sep='\t', header=None,
                     names=['date','time','open','high','low','close','tickvol','vol','spread'],
                     low_memory=False)
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y.%m.%d %H:%M:%S', errors='coerce')
    df = df.dropna(subset=['datetime'])
    df = df.drop(['date','time'], axis=1).set_index('datetime')
    for col in ['open','high','low','close','tickvol','vol','spread']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def read_h4():
    df = pd.read_csv('data/market_data/local_xau_h4.csv', sep='\t')
    df['datetime'] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'], format='%Y.%m.%d %H:%M:%S', errors='coerce')
    df = df.dropna(subset=['datetime'])
    df = df.rename(columns={
        '<OPEN>':'open','<HIGH>':'high','<LOW>':'low','<CLOSE>':'close',
        '<TICKVOL>':'tickvol','<VOL>':'vol','<SPREAD>':'spread'
    })
    df = df.drop(['<DATE>','<TIME>'], axis=1).set_index('datetime')
    for col in ['open','high','low','close','tickvol','vol','spread']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

m15 = read_m15()
h4 = read_h4()

print("M15 last date:", m15.index[-1])
print("H4 last date:", h4.index[-1])
print("M15 shape:", m15.shape)
print("H4 shape:", h4.shape)

last_m15 = m15.iloc[-1]
print("Latest M15 bar:", m15.index[-1], "O:", last_m15['open'], "H:", last_m15['high'], "L:", last_m15['low'], "C:", last_m15['close'])

# Resample to other TFs
m1 = m15.resample('1min').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
m5 = m15.resample('5min').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
h1 = m15.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()

print("Resampled shapes:")
print("M1:", m1.shape, "last:", m1.index[-1])
print("M5:", m5.shape, "last:", m5.index[-1])
print("H1:", h1.shape, "last:", h1.index[-1])

# Latest close per TF
for name, df in [("H4", h4), ("H1", h1), ("M15", m15), ("M5", m5), ("M1", m1)]:
    last = df.iloc[-1]
    print(f"{name} latest C={last['close']}")

# Simple trend check on M15: close vs ema20/ema50
m15['ema20'] = m15['close'].ewm(span=20, adjust=False).mean()
m15['ema50'] = m15['close'].ewm(span=50, adjust=False).mean()
print("M15 EMA20:", m15['ema20'].iloc[-1])
print("M15 EMA50:", m15['ema50'].iloc[-1])
print("M15 close > ema20:", m15['close'].iloc[-1] > m15['ema20'].iloc[-1])
print("M15 close > ema50:", m15['close'].iloc[-1] > m15['ema50'].iloc[-1])

# Check recent swing high/low on M15
last5 = m15.tail(5)
recent_high = last5['high'].max()
recent_low = last5['low'].min()
print("M15 last5 high:", recent_high, "low:", recent_low)

# Check H4 trend
h4['ema20'] = h4['close'].ewm(span=20, adjust=False).mean()
h4['ema50'] = h4['close'].ewm(span=50, adjust=False).mean()
print("H4 EMA20:", h4['ema20'].iloc[-1])
print("H4 EMA50:", h4['ema50'].iloc[-1])
print("H4 close > ema20:", h4['close'].iloc[-1] > h4['ema20'].iloc[-1])
print("H4 close > ema50:", h4['close'].iloc[-1] > h4['ema50'].iloc[-1])

# Simple setup check: close breaking above last 20-bar high (breakout)
m15['high20'] = m15['high'].rolling(20).max().shift(1)
m15['low20'] = m15['low'].rolling(20).min().shift(1)
last_row = m15.iloc[-1]
prev_high = m15['high20'].iloc[-1]
prev_low = m15['low20'].iloc[-1]
print("M15 prev 20-bar high:", prev_high)
print("M15 prev 20-bar low:", prev_low)
print("M15 close > prev_high20:", last_row['close'] > prev_high)
print("M15 close < prev_low20:", last_row['close'] < prev_low)
