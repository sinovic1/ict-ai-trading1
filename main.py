import logging
import asyncio
import pandas as pd
import yfinance as yf
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import numpy as np

TOKEN = "7134641176:AAHtLDFCIvlnXVQgX0CHWhbgFUfRyuhbmXU"
OWNER_ID = 7469299312  # Your Telegram user ID
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "USDCAD=X"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def calculate_indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["RSI"] = compute_rsi(df["Close"])
    df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    df["Upper"], df["Lower"] = bollinger_bands(df["Close"])
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def bollinger_bands(series, period=20, std_dev=2):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper, lower

def check_signals(df):
    signals = []
    close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2]

    # EMA
    ema_signal = "buy" if close > df["EMA20"].iloc[-1] else "sell"

    # RSI
    rsi = df["RSI"].iloc[-1]
    rsi_signal = "buy" if rsi < 30 else "sell" if rsi > 70 else "neutral"

    # MACD
    macd = df["MACD"].iloc[-1]
    signal = df["Signal"].iloc[-1]
    macd_signal = "buy" if macd > signal else "sell"

    # Bollinger Bands
    bb_signal = "buy" if close < df["Lower"].iloc[-1] else "sell" if close > df["Upper"].iloc[-1] else "neutral"

    signals.extend([ema_signal, rsi_signal, macd_signal, bb_signal])
    return signals

def decision(signals):
    buys = signals.count("buy")
    sells = signals.count("sell")
    if buys >= 2:
        return "buy"
    elif sells >= 2:
        return "sell"
    return None

def calculate_tp_sl(entry, direction):
    tp1 = round(entry * (1.002 if direction == "buy" else 0.998), 5)
    tp2 = round(entry * (1.004 if direction == "buy" else 0.996), 5)
    tp3 = round(entry * (1.006 if direction == "buy" else 0.994), 5)
    sl = round(entry * (0.996 if direction == "buy" else 1.004), 5)
    return tp1, tp2, tp3, sl

async def send_signal(context: ContextTypes.DEFAULT_TYPE, pair: str, signal: str, price: float):
    tp1, tp2, tp3, sl = calculate_tp_sl(price, signal)
    text = (
        f"📊 <b>{pair.replace('=X', '')} Signal</b>\n"
        f"📈 <b>Direction:</b> {signal.upper()}\n"
        f"🎯 <b>Entry:</b> {price}\n"
        f"✅ <b>TP1:</b> {tp1}\n"
        f"✅ <b>TP2:</b> {tp2}\n"
        f"✅ <b>TP3:</b> {tp3}\n"
        f"❌ <b>SL:</b> {sl}"
    )
    await context.bot.send_message(chat_id=OWNER_ID, text=text, parse_mode="HTML")

async def signal_loop(app: Application):
    while True:
        try:
            for pair in PAIRS:
                df = yf.download(pair, interval="5m", period="1d")
                if df.empty:
                    continue
                df = calculate_indicators(df)
                signals = check_signals(df)
                final_signal = decision(signals)
                price = round(df["Close"].iloc[-1], 5)

                if final_signal:
                    await send_signal(app, pair, final_signal, price)

            await asyncio.sleep(300)  # Wait 5 minutes
        except Exception as e:
            await app.bot.send_message(chat_id=OWNER_ID, text=f"❌ Bot crashed: {e}")
            break  # Stop the loop to trigger restart

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("✅ Bot is running and checking signals.")
    else:
        await update.message.reply_text("🚫 You're not authorized to use this bot.")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("status", status))

    # Start the signal loop
    asyncio.create_task(signal_loop(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())





