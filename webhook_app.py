"""webhook_app.py

FastAPI webhook endpoint for Telegram. Imports query_hf from hf_client and replies via Bot API.
Designed to deploy on Heroku/Railway where HTTPS is provided.
"""

import os
import requests
from fastapi import FastAPI, Request
from telegram import Bot, Update
from hf_client import query_hf

TELE_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELE_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN must be set as environment variable")
bot = Bot(TELE_TOKEN)
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/telegram_webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    if update.message and update.message.text:
        chat_id = update.message.chat.id
        prompt = update.message.text.strip()[:800]
        try:
            reply = query_hf(prompt)
        except Exception as e:
            reply = f"Error: {e}"
        try:
            bot.send_message(chat_id=chat_id, text=reply)
        except Exception:
            pass
    return {"ok": True}
