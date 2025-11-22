"""hf_client.py

Async Hugging Face client using Gemma-2-2b-it chat model.
"""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "google/gemma-2-2b-it:nebius")

if not HF_TOKEN:
    logger.error("HF_API_TOKEN environment variable not set!")

# OpenAI-compatible client for HF Router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# Simple in-memory cache (optional)
CACHE = {}
CACHE_MAX = 500

async def query_hf(prompt: str) -> str:
    """Query Gemma chat model via HF Inference Provider."""
    key = (HF_MODEL, prompt)
    if key in CACHE:
        return CACHE[key]

    try:
        # Note: client.chat.completions.create is synchronous, wrap in thread if truly async
        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        reply = completion.choices[0].message
    except Exception as e:
        logger.exception("Error querying HF: %s", e)
        raise

    # Manage cache
    if len(CACHE) >= CACHE_MAX:
        CACHE.pop(next(iter(CACHE)))
    CACHE[key] = reply
    return reply
