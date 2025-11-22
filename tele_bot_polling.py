"""tele_bot_polling.py

Polling-based Telegram bot for local development. Imports query_hf_sync from hf_client.
"""

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import asyncio
import logging

# Import the synchronous HF wrapper we designed to run in a thread
from hf_client import query_hf_sync

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELE_TOKEN = os.getenv("TELEGRAM_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello — polling bot ready. Send a message.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = (update.message.text or "").strip()[:1000]

    # Send a temporary "thinking" message
    thinking_msg = await update.message.reply_text("Thinking...")

    try:
        # Run the blocking HF call in a thread so the event loop isn't blocked
        reply = await asyncio.to_thread(query_hf_sync, prompt)

        # Ensure reply is a string
        if not isinstance(reply, str):
            reply = str(reply)

        # Edit the temporary message with the final reply
        await thinking_msg.edit_text(reply)
    except Exception as e:
        logger.exception("Error while querying HF or replying: %s", e)
        # Show friendly error to user
        try:
            await thinking_msg.edit_text(f"Error: {e}")
        except Exception:
            # fallback: send a new message if edit fails
            await update.message.reply_text(f"Error: {e}")


if __name__ == "__main__":
    if not TELE_TOKEN:
        print("ERROR: TELEGRAM_TOKEN not set. Copy .env.example -> .env and fill it")
        raise SystemExit(1)

    app = ApplicationBuilder().token(TELE_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Polling bot starting...")
    app.run_polling()
