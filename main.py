import asyncio
import nest_asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from indicators import analyze_pair
from config import (
    TELEGRAM_TOKEN,
    TELEGRAM_USER_ID,
    FOREX_PAIRS
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the scheduler
scheduler = AsyncIOScheduler()

# Main bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != TELEGRAM_USER_ID:
        return
    await update.message.reply_text("👋 Hello Hassan! I'm your trading bot. Type /status to check if I'm running.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != TELEGRAM_USER_ID:
        return
    await update.message.reply_text("✅ Everything is working fine.")

# Signal checker
async def check_signals(application):
    from signal_generator import generate_signal

    for pair in FOREX_PAIRS:
        try:
            result = await generate_signal(pair)
            if result:
                await application.bot.send_message(chat_id=TELEGRAM_USER_ID, text=result)
        except Exception as e:
            logger.error(f"Error checking signals for {pair}: {e}")

# Loop monitor
async def loop_monitor(application):
    try:
        await application.bot.send_message(chat_id=TELEGRAM_USER_ID, text="⚠️ Signal loop is not responding.")
    except Exception as e:
        logger.error(f"Failed to send loop warning: {e}")

# Main function
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))

    # Scheduled tasks
    scheduler.add_job(check_signals, "interval", seconds=300, args=[app])
    scheduler.add_job(loop_monitor, "interval", minutes=15, args=[app])
    scheduler.start()

    logger.info("✅ Bot started successfully.")
    await app.run_polling()

# Fix event loop issues for platforms like Koyeb
if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())

