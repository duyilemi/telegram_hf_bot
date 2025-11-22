"""webhook_app.py

FastAPI webhook for Telegram bot using Gemma chat model.
"""

import os
import logging
from fastapi import FastAPI, Request
from telegram import Bot, Update
from hf_client import query_hf  # async-compatible client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
bot = None

@app.on_event("startup")
async def startup_event():
    """Validate env and initialize Telegram bot."""
    global bot
    TELE_TOKEN = os.getenv("TELEGRAM_TOKEN")

    if not TELE_TOKEN:
        logger.error("Missing TELEGRAM_TOKEN environment variable.")
    else:
        logger.info("TELEGRAM_TOKEN present: %s", TELE_TOKEN[:4] + "..." + TELE_TOKEN[-4:])
        try:
            bot = Bot(TELE_TOKEN)
            logger.info("Telegram Bot initialized.")
        except Exception as e:
            logger.exception("Failed to initialize Telegram Bot: %s", e)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/debug_env")
def debug_env():
    return {
        "TELEGRAM_TOKEN_set": bool(os.getenv("TELEGRAM_TOKEN")),
        "HF_API_TOKEN_set": bool(os.getenv("HF_API_TOKEN")),
        "HF_MODEL": os.getenv("HF_MODEL")
    }

@app.post("/telegram_webhook")
async def telegram_webhook(request: Request):
    """Receive Telegram updates and reply using HF Gemma model."""
    data = await request.json()

    if bot is None:
        logger.error("Received update but Telegram Bot is not initialized.")
        return {"ok": False, "reason": "bot_not_initialized"}

    update = Update.de_json(data, bot)
    if update.message and update.message.text:
        chat_id = update.message.chat.id
        prompt = update.message.text.strip()[:800]

        try:
            # Wrap blocking call in thread to keep FastAPI async
            import asyncio
            reply = await asyncio.to_thread(query_hf, prompt)
        except Exception as e:
            logger.exception("Error querying HF: %s", e)
            reply = "Sorry, I couldn't reach the model right now."

        try:
            await bot.send_message(chat_id=chat_id, text=reply)
        except Exception:
            logger.exception("Failed to send message to Telegram user %s", chat_id)

    return {"ok": True}
