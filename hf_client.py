"""hf_client.py

Async Hugging Face client with in-memory caching.
Used by both polling and webhook apps.
"""

import os
import httpx
import logging

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_API_TOKEN")
MODEL_ID = os.getenv("HF_MODEL", "google/flan-t5-small-v2")  # updated default
HF_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# Simple in-memory cache
CACHE = {}
CACHE_MAX = 500

async def query_hf(prompt: str, max_tokens: int = 150, timeout: int = 30) -> str:
    """Async query to HF Inference API with caching."""
    if not HF_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not set")

    key = (MODEL_ID, prompt)
    if key in CACHE:
        return CACHE[key]

    payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(HF_URL, headers=HEADERS, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        logger.exception("HF API returned error: %s", e)
        raise
    except Exception as e:
        logger.exception("Error querying HF: %s", e)
        raise

    # Extract generated_text
    if isinstance(data, list) and data and "generated_text" in data[0]:
        out = data[0]["generated_text"]
    elif isinstance(data, dict) and "generated_text" in data:
        out = data["generated_text"]
    else:
        out = str(data)

    # Manage cache size
    if len(CACHE) >= CACHE_MAX:
        CACHE.pop(next(iter(CACHE)))
    CACHE[key] = out
    return out
