import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN", "7923000946:AAEx8TZsaIl6GL7XUwPGEM6a6-mBNfKwUz8")
AUTHORIZED_USER_ID = 7469299312

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

TRADING_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD",
    "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "XAUUSD"
]

def generate_signal(pair):
    direction = random.choice(["BUY", "SELL"])
    entry = round(random.uniform(1.1000, 1.2000), 5)
    tp1 = round(entry + 0.0020 if direction == "BUY" else entry - 0.0020, 5)
    tp2 = round(entry + 0.0040 if direction == "BUY" else entry - 0.0040, 5)
    tp3 = round(entry + 0.0060 if direction == "BUY" else entry - 0.0060, 5)
    sl = round(entry - 0.0020 if direction == "BUY" else entry + 0.0020, 5)
    return f"<b>{pair} Signal</b>
Direction: <b>{direction}</b>
Entry: <b>{entry}</b>
TP1: {tp1}
TP2: {tp2}
TP3: {tp3}
SL: {sl}"

async def check_strategies():
    for pair in TRADING_PAIRS:
        if random.random() < 0.05:
            signal = generate_signal(pair)
            await bot.send_message(AUTHORIZED_USER_ID, signal)

@dp.message(Command("start"))
async def start(message: Message):
    if message.from_user.id == AUTHORIZED_USER_ID:
        await message.answer("✅ Bot is running and you're authorized.")
    else:
        await message.answer("⛔ You are not authorized to use this bot.")

@dp.message(Command("status"))
async def status(message: Message):
    if message.from_user.id == AUTHORIZED_USER_ID:
        await message.answer("✅ Everything is working fine.")
    else:
        await message.answer("⛔ You are not authorized.")

async def main():
    scheduler.add_job(check_strategies, "interval", minutes=2)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())