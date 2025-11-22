# hf_client.py
"""Synchronous HF client wrapper for Gemma chat model.
   Use asyncio.to_thread() from webhook to keep FastAPI event loop responsive.
"""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "google/gemma-2-2b-it:nebius")

if not HF_TOKEN:
    logger.error("HF_API_TOKEN environment variable not set!")

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# Simple in-memory cache (optional)
CACHE = {}
CACHE_MAX = 500

def query_hf_sync(prompt: str) -> str:
    """Synchronous function that queries the HF router (blocking)."""
    key = (HF_MODEL, prompt)
    if key in CACHE:
        return CACHE[key]

    try:
        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=[{"role": "user", "content": prompt}],
            # you can add max_tokens, temperature, etc. here as kwargs
        )
        # completion.choices[0].message is an object; convert to string
        # In many clients it's completion.choices[0].message["content"] or .content
        # Use repr that matches what your client returns:
        choice = completion.choices[0].message
        # If it's a dict-like:
        reply_text = choice.get("content") if isinstance(choice, dict) and "content" in choice else str(choice)
    except Exception as e:
        logger.exception("Error querying HF: %s", e)
        raise

    # manage cache
    if len(CACHE) >= CACHE_MAX:
        CACHE.pop(next(iter(CACHE)))
    CACHE[key] = reply_text
    return reply_text
