import yfinance as yf
import pandas as pd

def check_signals():
    forex_pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDCHF=X', 'AUDUSD=X', 'USDCAD=X']
    signals = []

    for pair in forex_pairs:
        data = yf.download(tickers=pair, period="7d", interval="1h", progress=False)

        if len(data) < 100:
            continue

        data['EMA'] = data['Close'].ewm(span=14, adjust=False).mean()
        delta = data['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))

        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = exp1 - exp2
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

        data['Upper'], data['Lower'] = data['Close'].rolling(window=20).mean(), data['Close'].rolling(window=20).std()
        data['BB_upper'] = data['Upper'] + (data['Lower'] * 2)
        data['BB_lower'] = data['Upper'] - (data['Lower'] * 2)

        latest = data.iloc[-1]
        confirmations = []

        if latest['RSI'] < 30:
            confirmations.append('RSI')
        if latest['MACD'] > latest['Signal']:
            confirmations.append('MACD')
        if latest['Close'] > latest['EMA']:
            confirmations.append('EMA')
        if latest['Close'] < latest['BB_lower']:
            confirmations.append('Bollinger Bands')

        if len(confirmations) >= 2:
            entry = latest['Close']
            signal = {
                'pair': pair.replace('=X', ''),
                'entry': round(entry, 5),
                'tp1': round(entry * 1.002, 5),
                'tp2': round(entry * 1.004, 5),
                'tp3': round(entry * 1.006, 5),
                'sl': round(entry * 0.996, 5),
                'strategy': ", ".join(confirmations)
            }
            signals.append(signal)

    return signals

def check_health():
    return True
