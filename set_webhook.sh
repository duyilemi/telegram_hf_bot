#!/usr/bin/env bash
# Usage: ./set_webhook.sh https://your-app-url.com
# Make executable: chmod +x set_webhook.sh

if [ -z "$1" ]; then
  echo "Usage: $0 https://your-app-url.com"
  exit 1
fi

URL=$1

if [ -z "$TELEGRAM_TOKEN" ]; then
  echo "ERROR: TELEGRAM_TOKEN must be exported in your shell or set in CI vars."
  exit 1
fi

# Post webhook URL to Telegram. We append /telegram_webhook to match your FastAPI endpoint.
curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
  -d "url=${URL}/telegram_webhook"
