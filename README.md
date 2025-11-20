# Telegram + Hugging Face Bot

This repository contains two modes for running a Telegram bot that uses Hugging Face Inference API:

- `tele_bot_polling.py` — Polling mode for local development (easy, no public URL required).
- `webhook_app.py` — Webhook mode (FastAPI) for deployment (Heroku / Railway).

Shared HF logic is in `hf_client.py` so both modes reuse the same code.

## Quick start (local polling)

1. Copy `.env.example` to `.env` and fill tokens.
2. Create a virtualenv or conda env and install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the polling bot:
   ```bash
   python tele_bot_polling.py
   ```

## Deploy webhook (Heroku / Railway)
1. Set TELEGRAM_TOKEN and HF_API_TOKEN as environment variables on the host.
2. Deploy the app (Heroku example):
   ```bash
   git push heroku main
   heroku config:set TELEGRAM_TOKEN=... HF_API_TOKEN=... HF_MODEL=google/flan-t5-small
   ./set_webhook.sh https://<your-heroku-app>.herokuapp.com
   ```

## Notes
- Do not commit `.env` to version control.
