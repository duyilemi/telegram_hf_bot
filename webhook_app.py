# webhook_app.py  -- safer startup checks, non-crashing import
import os
import requests
import logging
from fastapi import FastAPI, Request
from telegram import Bot, Update
from hf_client import query_hf  # shared HF logic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# We'll create the Bot object lazily on startup after env checks
bot = None

@app.on_event("startup")
async def startup_event():
    """Validate environment and initialize resources - runs after import."""
    global bot
    TELE_TOKEN = os.getenv("TELEGRAM_TOKEN")
    HF_TOKEN = os.getenv("HF_API_TOKEN")

    # Basic presence checks - don't crash, just log helpful errors
    if not TELE_TOKEN:
        logger.error("Missing TELEGRAM_TOKEN environment variable.")
    else:
        # log a masked version so you can confirm it exists in logs without exposing it
        logger.info("TELEGRAM_TOKEN present: %s", TELE_TOKEN[:4] + "..." + TELE_TOKEN[-4:])

    if not HF_TOKEN:
        logger.error("Missing HF_API_TOKEN environment variable.")
    else:
        logger.info("HF_API_TOKEN present: %s", HF_TOKEN[:4] + "..." + HF_TOKEN[-4:])

    # If tokens are present, initialize Bot (this will raise if token invalid later when used)
    if TELE_TOKEN:
        try:
            bot = Bot(TELE_TOKEN)  # lazy init
            logger.info("Telegram Bot initialized.")
        except Exception as e:
            # init failure should not crash the import; log and keep running
            logger.exception("Failed to initialize Telegram Bot: %s", e)

@app.get("/health")
def health():
    """Simple health endpoint."""
    return {"status": "ok"}

@app.get("/debug_env")
def debug_env():
    """Return presence flags for env vars (no secrets). Useful for deployment debugging."""
    return {
        "TELEGRAM_TOKEN_set": bool(os.getenv("TELEGRAM_TOKEN")),
        "HF_API_TOKEN_set": bool(os.getenv("HF_API_TOKEN")),
        "HF_MODEL": os.getenv("HF_MODEL")
    }

@app.post("/telegram_webhook")
async def telegram_webhook(request: Request):
    """Receive Telegram updates and reply using HF model."""
    data = await request.json()
    if bot is None:
        # If bot hasn't been initialized, return 200 so Telegram won't retry too fast;
        # but also log so we can see problem in logs.
        logger.error("Received update but Telegram Bot is not initialized.")
        return {"ok": False, "reason": "bot_not_initialized"}

    update = Update.de_json(data, bot)
    if update.message and update.message.text:
        chat_id = update.message.chat.id
        prompt = update.message.text.strip()[:800]

        try:
            # Query shared HF client (may raise on network / quota errors)
            reply = query_hf(prompt)
        except Exception as e:
            logger.exception("Error querying HF: %s", e)
            reply = "Sorry, I couldn't reach the model right now."

        # Send reply, but swallow exceptions so webhook endpoint remains responsive
        try:
            bot.send_message(chat_id=chat_id, text=reply)
        except Exception:
            logger.exception("Failed to send message to Telegram user %s", chat_id)

    return {"ok": True}
