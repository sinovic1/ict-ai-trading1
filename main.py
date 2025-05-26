import asyncio
import logging
import nest_asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import os

# Telegram bot token and user ID (your ID only)
BOT_TOKEN = "7134641176:AAHtLDFCIvlnXVQgX0CHWhbgFUfRyuhbmXU"
OWNER_ID = 7469299312

# Forex pairs to track
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "USDCAD=X"]

# Logger setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Check if the user is authorized
def is_authorized(user_id: int) -> bool:
    return user_id == OWNER_ID

# Calculate indicators
def calculate_indicators(df: pd.DataFrame) -> dict:
    signals = {}

    # EMA
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    ema_signal = "buy" if df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1] else "sell"

    # RSI
    delta = df["Close"].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_value = rsi.iloc[-1]
    rsi_signal = "buy" if rsi_value < 30 else "sell" if rsi_value > 70 else "neutral"

    # MACD
    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=9, adjust=False).mean()
    macd_signal = "buy" if macd.iloc[-1] > signal_line.iloc[-1] else "sell"

    # Bollinger Bands
    sma = df["Close"].rolling(window=20).mean()
    std = df["Close"].rolling(window=20).std()
    upper_band = sma + 2 * std
    lower_band = sma - 2 * std
    price = df["Close"].iloc[-1]
    bb_signal = "buy" if price < lower_band.iloc[-1] else "sell" if price > upper_band.iloc[-1] else "neutral"

    # Count strong signals
    signal_votes = [ema_signal, rsi_signal, macd_signal, bb_signal]
    buy_votes = signal_votes.count("buy")
    sell_votes = signal_votes.count("sell")

    if buy_votes >= 2:
        signal = "buy"
    elif sell_votes >= 2:
        signal = "sell"
    else:
        signal = None

    if signal:
        entry = df["Close"].iloc[-1]
        if signal == "buy":
            tp1 = entry + 0.0020
            tp2 = entry + 0.0040
            tp3 = entry + 0.0060
            sl = entry - 0.0025
        else:
            tp1 = entry - 0.0020
            tp2 = entry - 0.0040
            tp3 = entry - 0.0060
            sl = entry + 0.0025

        signals = {
            "pair": df.attrs["pair"],
            "signal": signal,
            "entry": round(entry, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "sl": round(sl, 5),
        }

    return signals

# Signal loop that runs continuously
async def signal_loop(app):
    while True:
        try:
            for pair in PAIRS:
                data = yf.download(pair, period="7d", interval="1h", auto_adjust=True)
                if data.empty:
                    continue
                data.attrs["pair"] = pair
                result = calculate_indicators(data)
                if result:
                    message = (
                        f"📈 *{result['pair']}* - *{result['signal'].upper()}*\n"
                        f"Entry: `{result['entry']}`\n"
                        f"Take Profit 1: `{result['tp1']}`\n"
                        f"Take Profit 2: `{result['tp2']}`\n"
                        f"Take Profit 3: `{result['tp3']}`\n"
                        f"Stop Loss: `{result['sl']}`"
                    )
                    await app.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode="Markdown")
        except Exception as e:
            await app.bot.send_message(chat_id=OWNER_ID, text=f"⚠️ Bot error: {e}")
        await asyncio.sleep(3600)  # Check every 1 hour

# /status command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_authorized(update.effective_user.id):
        await update.message.reply_text("✅ Bot is running and checking signals.")
    else:
        await update.message.reply_text("❌ Unauthorized user.")

# Main async function
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("status", status))

    # Start the signal loop
    asyncio.create_task(signal_loop(app))

    # Run the bot
    await app.run_polling()

# Event loop fix for environments like Koyeb
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop is already running" in str(e):
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise





