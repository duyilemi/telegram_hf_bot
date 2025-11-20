"""tele_bot_polling.py

Polling-based Telegram bot for local development. Imports query_hf from hf_client.
"""

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import os
from hf_client import query_hf

load_dotenv()
TELE_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context):
    await update.message.reply_text("Hello — polling bot ready. Send a message.")

async def handle_message(update: Update, context):
    prompt = (update.message.text or "").strip()[:1000]
    thinking = await update.message.reply_text("Thinking...")
    try:
        reply = query_hf(prompt)
        await thinking.edit_text(reply)
    except Exception as e:
        await thinking.edit_text(f"Error: {e}")

if __name__ == "__main__":
    if not TELE_TOKEN:
        print("ERROR: TELEGRAM_TOKEN not set. Copy .env.example -> .env and fill it")
    app = ApplicationBuilder().token(TELE_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Polling bot starting...")
    app.run_polling()
