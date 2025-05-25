import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from utils import is_authorized, format_signal
from logic import check_signals, check_health

TOKEN = "7923000946:AAEx8TZsaIl6GL7XUwPGEM6a6-mBNfKwUz8"
AUTHORIZED_USER_ID = 7469299312

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text("🤖 Bot is running and ready to give signals!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text("✅ Everything is working fine.")

async def signal_loop(application):
    while True:
        try:
            logging.info("🔄 Checking for signals...")
            signals = check_signals()
            for signal in signals:
                formatted = format_signal(signal)
                await application.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=formatted)
        except Exception as e:
            logging.error(f"Error in signal loop: {e}")
        await asyncio.sleep(300)  # 5 minutes

async def health_check_loop(application):
    while True:
        try:
            healthy = check_health()
            if not healthy:
                await application.bot.send_message(chat_id=AUTHORIZED_USER_ID, text="⚠️ Bot might have stopped working!")
        except Exception as e:
            logging.error(f"Health check error: {e}")
        await asyncio.sleep(600)  # 10 minutes

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))

    # Start loops
    asyncio.create_task(signal_loop(app))
    asyncio.create_task(health_check_loop(app))

    await app.run_polling()

# Safe for environments with already running event loops (e.g., Koyeb)
try:
    asyncio.get_event_loop().run_until_complete(main())
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
