import asyncio
import logging
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta

TOKEN = "7923000946:AAEx8TZsaIl6GL7XUwPGEM6a6-mBNfKwUz8"
ALLOWED_USER_ID = 7469299312
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "USDCAD=X"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

last_signal_time = {}

# === STRATEGIES ===

def rsi(data, period=14):
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(data):
    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line - signal

def bollinger_bands(data, window=20):
    sma = data["Close"].rolling(window).mean()
    std = data["Close"].rolling(window).std()
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    return upper, lower

def ema(data, span=20):
    return data["Close"].ewm(span=span, adjust=False).mean()

def check_signals(df):
    if df.isnull().values.any():
        return None

    signals = []

    rsi_val = rsi(df).iloc[-1]
    if rsi_val < 30:
        signals.append("BUY")
    elif rsi_val > 70:
        signals.append("SELL")

    macd_val = macd(df).iloc[-1]
    if macd_val > 0:
        signals.append("BUY")
    elif macd_val < 0:
        signals.append("SELL")

    upper, lower = bollinger_bands(df)
    last_close = df["Close"].iloc[-1]
    if last_close < lower.iloc[-1]:
        signals.append("BUY")
    elif last_close > upper.iloc[-1]:
        signals.append("SELL")

    ema_val = ema(df).iloc[-1]
    if last_close > ema_val:
        signals.append("BUY")
    elif last_close < ema_val:
        signals.append("SELL")

    buy_count = signals.count("BUY")
    sell_count = signals.count("SELL")

    if buy_count >= 2:
        return "BUY"
    elif sell_count >= 2:
        return "SELL"
    return None

# === BOT ===

async def send_signal(context: ContextTypes.DEFAULT_TYPE, pair: str, signal: str, price: float):
    tp1 = price + 0.002 if signal == "BUY" else price - 0.002
    tp2 = price + 0.004 if signal == "BUY" else price - 0.004
    tp3 = price + 0.006 if signal == "BUY" else price - 0.006
    sl = price - 0.0015 if signal == "BUY" else price + 0.0015

    msg = (
        f"📉 *{pair.replace('=X','')}* Signal\n"
        f"Signal: *{signal}*\n"
        f"Entry: `{price:.5f}`\n"
        f"TP1: `{tp1:.5f}`\n"
        f"TP2: `{tp2:.5f}`\n"
        f"TP3: `{tp3:.5f}`\n"
        f"SL: `{sl:.5f}`"
    )
    await context.bot.send_message(chat_id=ALLOWED_USER_ID, text=msg, parse_mode="Markdown")

async def check_loop(context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔄 Checking for signals...")
    for pair in PAIRS:
        try:
            df = yf.download(pair, period="2d", interval="15m", progress=False)
            if df.empty or len(df) < 30:
                continue

            signal = check_signals(df)
            price = df["Close"].iloc[-1]

            now = datetime.utcnow()
            last_time = last_signal_time.get(pair)
            if signal and (not last_time or now - last_time > timedelta(minutes=30)):
                await send_signal(context, pair, signal, price)
                last_signal_time[pair] = now

        except Exception as e:
            logger.error(f"Error in signal loop: {e}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ALLOWED_USER_ID:
        await update.message.reply_text("✅ Bot is running and checking signals.")
    else:
        await update.message.reply_text("⛔ You are not authorized.")

async def health_check(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.utcnow()
    if not any(last_signal_time.values()) or max(last_signal_time.values()) < now - timedelta(minutes=60):
        await context.bot.send_message(chat_id=ALLOWED_USER_ID, text="⚠️ WARNING: Signal loop may have stopped!")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("status", status))
    app.job_queue.run_repeating(check_loop, interval=60, first=5)
    app.job_queue.run_repeating(health_check, interval=300, first=60)
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

