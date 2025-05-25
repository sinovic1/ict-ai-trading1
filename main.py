import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import os

# Telegram bot token and user ID
TOKEN = "7923000946:AAEx8TZsaIl6GL7XUwPGEM6a6-mBNfKwUz8"
OWNER_ID = 7469299312

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def generate_signal(pair: str) -> str:
    return f"<b>{pair} Signal</b>"  # ✅ Fixed string literal

# Command handler
async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return

    pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"]
    for pair in pairs:
        signal = generate_signal(pair)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=signal,
            parse_mode="HTML"
        )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    await update.message.reply_text("✅ Everything is working fine.")

async def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("signal", signal_command))
    app.add_handler(CommandHandler("status", status_command))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
