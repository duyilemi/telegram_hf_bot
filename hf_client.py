"""hf_client.py

Shared Hugging Face client: queries the HF Inference API and provides a small in-memory cache.
Both polling and webhook apps import and use `query_hf`.
"""

import os
import requests

HF_TOKEN = os.getenv("HF_API_TOKEN")
MODEL_ID = os.getenv("HF_MODEL", "google/flan-t5-small")
HF_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# Simple in-memory cache for demo purposes
CACHE = {}
CACHE_MAX = 500

def query_hf(prompt: str, max_tokens: int = 150, timeout: int = 30) -> str:
    """Query HF Inference API and return generated text.

    Returns a string. Raises requests.HTTPError on non-2xx responses.
    """
    if not HF_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not set")
    key = (MODEL_ID, prompt)
    if key in CACHE:
        return CACHE[key]
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}
    resp = requests.post(HF_URL, headers=HEADERS, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list) and data and "generated_text" in data[0]:
        out = data[0]["generated_text"]
    elif isinstance(data, dict) and "generated_text" in data:
        out = data["generated_text"]
    else:
        out = str(data)
    if len(CACHE) >= CACHE_MAX:
        CACHE.pop(next(iter(CACHE)))
    CACHE[key] = out
    return out
