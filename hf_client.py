import re
import logging
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "google/gemma-2-2b-it:nebius")

client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=HF_TOKEN)

# optional cache
CACHE = {}
CACHE_MAX = 500

def _extract_text_from_choice(choice) -> str:
    """Try to extract the textual assistant reply from various possible shapes.

    Handles:
      - dicts like {"content": "..."} or {"message": {"content": "..."}}
      - objects with .content or .message attributes
      - stringified ChatCompletionMessage(...) reprs
      - fall back to str(choice)
    """
    # 1) dict-like
    if isinstance(choice, dict):
        # common places
        if "content" in choice and isinstance(choice["content"], str):
            return choice["content"]
        if "message" in choice:
            msg = choice["message"]
            if isinstance(msg, dict) and "content" in msg:
                return msg["content"]
            # if message is already a string
            if isinstance(msg, str):
                return msg

    # 2) objects with attributes (.content, .message)
    if hasattr(choice, "content"):
        try:
            val = getattr(choice, "content")
            if isinstance(val, str):
                return val
            # sometimes .content is itself dict-like
            if isinstance(val, dict) and "content" in val:
                return val["content"]
            return str(val)
        except Exception:
            pass

    if hasattr(choice, "message"):
        try:
            msg = getattr(choice, "message")
            # message could be dict-like or object
            if isinstance(msg, dict) and "content" in msg:
                return msg["content"]
            if hasattr(msg, "content"):
                return getattr(msg, "content")
            return str(msg)
        except Exception:
            pass

    # 3) fallback: if it's already a plain string, return it
    if isinstance(choice, str):
        # If it's the ChatCompletionMessage(...) string, try to extract content='...'
        # regex searches for content='...' or content="..."
        m = re.search(r"content=(?P<q>['\"])(?P<text>.*?)(?P=q)(?:,|\))", choice, re.DOTALL)
        if m:
            return m.group("text")
        # otherwise return the whole string
        return choice

    # 4) final fallback
    return str(choice)


def _clean_text(text: str) -> str:
    """Lightweight cleaning:
       - strip whitespace
       - collapse repeated newlines to single newline
       - remove leading/trailing quotes
       - optionally remove surrounding markdown code fences
       - remove excessive whitespace
    """
    if not isinstance(text, str):
        text = str(text)
    # strip surrounding quotes
    text = text.strip()
    # remove triple-backtick fences
    text = re.sub(r"^```(?:\w+)?\n", "", text)
    text = re.sub(r"\n```$", "", text)
    # collapse multiple newlines to one
    text = re.sub(r"\n{2,}", "\n\n", text)
    # collapse many spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    # remove weird leading/trailing quotes and whitespace again
    text = text.strip(' \n"\'')
    return text


def query_hf_sync(prompt: str) -> str:
    """Synchronous function that queries the HF router (blocking) and returns clean text."""
    key = (HF_MODEL, prompt)
    if key in CACHE:
        return CACHE[key]

    try:
        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=[{"role": "user", "content": prompt}],
            # add parameters like max_tokens, temperature if you want
        )
        # the 'choices' structure can vary; handle common variations
        if hasattr(completion, "choices") and completion.choices:
            choice0 = completion.choices[0]
            # sometimes the message is at choice0.message, sometimes at choice0["message"], etc
            reply_raw = None
            # try attribute access
            try:
                reply_raw = getattr(choice0, "message", None) or getattr(choice0, "text", None) or getattr(choice0, "content", None) or choice0
            except Exception:
                reply_raw = choice0
        elif isinstance(completion, dict) and "choices" in completion and completion["choices"]:
            choice0 = completion["choices"][0]
            reply_raw = choice0.get("message") or choice0.get("text") or choice0
        else:
            # fallback: stringify whole completion
            reply_raw = completion

        # extract textual content
        reply_text = _extract_text_from_choice(reply_raw)
        reply_text = _clean_text(reply_text)

    except Exception as e:
        logger.exception("Error querying HF: %s", e)
        raise

    # cache and return
    if len(CACHE) >= CACHE_MAX:
        CACHE.pop(next(iter(CACHE)))
    CACHE[key] = reply_text
    return reply_text
