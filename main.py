import time
import logging
import requests
import pandas as pd
import numpy as np
import ta
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import threading

# === CONFIG ===
TOKEN = "7923000946:AAEx8TZsaIl6GL7XUwPGEM6a6-mBNfKwUz8"
ALLOWED_USER_ID = 7469299312
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"]
INTERVAL = "5min"
CHECK_INTERVAL = 300  # 5 minutes in seconds

bot = Bot(token=TOKEN)

def analyze_pair(df):
    df = df.copy()
    if df is None or len(df) < 50:
        return None

    # Indicators
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd_diff'] = macd.macd_diff()
    df['ema_20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    bb = ta.volatility.BollingerBands(df['close'])
    df['upper_band'] = bb.bollinger_hband()
    df['lower_band'] = bb.bollinger_lband()

    latest = df.iloc[-1]

    signals = []
    if latest['rsi'] < 30:
        signals.append("RSI")
    if latest['macd_diff'] > 0:
        signals.append("MACD")
    if latest['close'] > latest['ema_20']:
        signals.append("EMA")
    if latest['close'] < latest['lower_band']:
        signals.append("Bollinger Bands")

    if len(signals) >= 2:
        entry = latest['close']
        return {
            "entry": entry,
            "tp1": round(entry * 1.002, 5),
            "tp2": round(entry * 1.004, 5),
            "tp3": round(entry * 1.006, 5),
            "sl": round(entry * 0.996, 5),
            "reasons": signals
        }
    return None

def get_price_data(pair):
    try:
        url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={pair[:3]}&to_symbol={pair[3:]}&interval={INTERVAL}&apikey=demo"
        r = requests.get(url)
        data = r.json()
        key = list(data.keys())[1]
        df = pd.DataFrame(data[key]).T.astype(float)
        df.columns = ["open", "high", "low", "close"]
        df = df.sort_index()
        return df
    except Exception as e:
        print(f"Error fetching {pair}: {e}")
        return None

def send_signal(pair, analysis):
    message = (
        f"📈 *{pair}* Signal\n"
        f"Entry: {analysis['entry']}\n"
        f"TP1: {analysis['tp1']}\n"
        f"TP2: {analysis['tp2']}\n"
        f"TP3: {analysis['tp3']}\n"
        f"SL: {analysis['sl']}\n"
        f"🧠 Reasons: {', '.join(analysis['reasons'])}"
    )
    bot.send_message(chat_id=ALLOWED_USER_ID, text=message, parse_mode="Markdown")

def check_signals():
    while True:
        try:
            for pair in PAIRS:
                df = get_price_data(pair)
                if df is not None:
                    analysis = analyze_pair(df)
                    if analysis:
                        send_signal(pair, analysis)
        except Exception as e:
            bot.send_message(chat_id=ALLOWED_USER_ID, text=f"❌ Bot Error: {e}")
        time.sleep(CHECK_INTERVAL)

def status(update: Update, context: CallbackContext):
    if update.effective_user.id == ALLOWED_USER_ID:
        context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Bot is running.")

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("status", status))
    updater.start_polling()
    threading.Thread(target=check_signals, daemon=True).start()
    updater.idle()

if __name__ == "__main__":
    main()


