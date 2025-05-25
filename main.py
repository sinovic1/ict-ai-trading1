import asyncio
import logging
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from logic import check_signals

# Telegram bot token and user ID
TOKEN = os.getenv("BOT_TOKEN", "7923000946:AAEx8TZsaIl6GL7XUwPGEM6a6-mBNfKwUz8")
AUTHORIZED_USER_ID = 7469299312

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

running = True  # Watchdog variable

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text("🤖 Bot is running and monitoring signals.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text("✅ Everything is working fine.")

def format_signal(pair, signal_data):
    direction = signal_data["signal"]
    entry = signal_data["entry"]
    sl = signal_data["sl"]
    tp1 = signal_data["tp1"]
    tp2 = signal_data["tp2"]
    tp3 = signal_data["tp3"]
    return f"<b>{pair} Signal</b>\nDirection: <b>{direction}</b>\nEntry: {entry}\nSL: {sl}\nTP1: {tp1}\nTP2: {tp2}\nTP3: {tp3}"

async def signal_loop(application: Application):
    global running
    try:
        while running:
            signals = check_signals()
            for pair, signal_data in signals.items():
                message = format_signal(pair, signal_data)
                await application.bot.send_message(
                    chat_id=AUTHORIZED_USER_ID, text=message, parse_mode=ParseMode.HTML
                )
            await asyncio.sleep(60)  # Wait 60 seconds between checks
    except Exception as e:
        running = False
        await application.bot.send_message(
            chat_id=AUTHORIZED_USER_ID,
            text=f"⚠️ Bot has stopped due to an error:\n{e}",
        )
        logger.error("Signal loop crashed", exc_info=True)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    # Start the signal-checking loop in background
    asyncio.create_task(signal_loop(app))
    await app.run_polling()

# Run with safe event loop handling
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
