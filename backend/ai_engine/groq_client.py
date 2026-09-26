"""
GroqAIAgent — Calls the Groq API and returns parsed content.
Includes Model Rotation and Phase-Based Quota Management.
"""
import json
import logging
import time
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from django.conf import settings

logger = logging.getLogger(__name__)

# Primary models for rotation on the Free Tier
DEFAULT_MODEL_POOL = [
    'openai/gpt-oss-120b',
    'openai/gpt-oss-20b',
    'qwen/qwen3.8-27b',
]

FALLBACK_MODEL = 'openai/gpt-oss-20b'
GROQ_CHAT_COMPLETIONS_URL = 'https://api.groq.com/openai/v1/chat/completions'

# In-memory cooldown tracking: {model_name: timestamp_when_available}
_MODEL_COOLDOWN = {}
COOLDOWN_BURST_SECONDS = 60          # 1 minute cooldown for temporary rate limit (RPM/TPM)
COOLDOWN_DAILY_QUOTA_SECONDS = 3600  # 1 hour cooldown for daily quota exhaustion (RPD/TPD)


def _mark_model_cooldown(model: str, is_daily_quota: bool = False):
    """Marks a model as cooling down so subsequent calls skip directly to working models."""
    duration = COOLDOWN_DAILY_QUOTA_SECONDS if is_daily_quota else COOLDOWN_BURST_SECONDS
    _MODEL_COOLDOWN[model] = time.time() + duration
    logger.warning(f"[Groq AI] Model {model} placed in cooldown for {duration}s (daily_quota={is_daily_quota})")


def _get_active_pool(preferred_model: str = None) -> list:
    """
    Returns ordered model candidates.
    Models NOT currently cooling down come first, followed by cooling models as last resort.
    """
    now = time.time()
    pool = list(DEFAULT_MODEL_POOL)
    if preferred_model:
        if preferred_model in pool:
            pool.remove(preferred_model)
        pool.insert(0, preferred_model)

    available = [m for m in pool if _MODEL_COOLDOWN.get(m, 0) <= now]
    cooling = [m for m in pool if _MODEL_COOLDOWN.get(m, 0) > now]
    return available if available else cooling


def _call_groq_http(system_prompt: str, user_prompt: str, model: str, max_tokens: int = 3500) -> dict:
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': 0.7,
        'max_tokens': max_tokens,
    }

    req = urlrequest.Request(
        GROQ_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {settings.GROQ_API_KEY}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        method='POST',
    )

    with urlrequest.urlopen(req, timeout=90) as resp:
        body = resp.read().decode('utf-8')
        return json.loads(body)


def call_groq(system_prompt: str, user_prompt: str, max_retries: int = 6, preferred_model: str = None, max_tokens: int = 3500) -> dict:
    """
    Calls Groq API with intelligent Model Rotation and Quota Management.
    If a rate limit (RPM), daily quota (RPD/TPD), or model error occurs:
    Automatically rotates to the next model in the pool seamlessly.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError('GROQ_API_KEY is not configured.')

    pool = _get_active_pool(preferred_model=preferred_model)
    current_model_idx = 0
    last_error = None

    for attempt in range(max_retries):
        model = pool[current_model_idx % len(pool)]
        try:
            logger.info(f"Groq API call attempt {attempt + 1}/{max_retries} using model: {model}")

            response = _call_groq_http(system_prompt, user_prompt, model, max_tokens=max_tokens)
            raw_text = (response.get('choices', [{}])[0].get('message', {}).get('content', '') or '').strip()
            tokens_used = (response.get('usage') or {}).get('total_tokens')

            if not raw_text:
                raise ValueError('Groq response did not include message content.')

            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                raw_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            parsed = json.loads(raw_text)
            return {"content": parsed, "tokens_used": tokens_used, "model_used": model}

        except json.JSONDecodeError as e:
            last_error = f"JSON parse error: {e}"
            logger.warning(f"Attempt {attempt + 1} failed with {model}: {last_error}")
            current_model_idx += 1
            if attempt < max_retries - 1:
                time.sleep(1)

        except HTTPError as e:
            try:
                err_body = e.read().decode('utf-8')
            except Exception:
                err_body = ''
            last_error = f"HTTP {e.code}: {err_body or e.reason}"

            if e.code == 403 and '1010' in last_error:
                raise PermissionError('Groq access denied (HTTP 403 / code 1010). Check region/network.')

            logger.warning(f"Attempt {attempt + 1} failed with {model}: {last_error}")

            # Check if quota / rate limit was hit
            err_lower = last_error.lower()
            is_daily_quota = any(term in err_lower for term in ['per day', 'rpd', 'tpd', 'quota'])
            
            # Rotate model on 429, 404, 400, 500, 502, 503, 504
            _mark_model_cooldown(model, is_daily_quota=is_daily_quota)
            current_model_idx += 1
            next_model = pool[current_model_idx % len(pool)]
            logger.info(f"Rotating from {model} to {next_model}...")

            if attempt < max_retries - 1:
                # If switching models on rate limit, a 1-2s delay is plenty since next model has separate quota
                time.sleep(1.5 if e.code == 429 else 1.0)

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1} failed with {model}: {last_error}")
            current_model_idx += 1
            if attempt < max_retries - 1:
                time.sleep(1)

    raise ValueError(f"Groq API failed after {max_retries} attempts with rotation. Last error: {last_error}")


def verify_prompt_safety(prompt: str, model: str = "meta-llama/llama-prompt-guard-2-86m", **kwargs) -> bool:
    """Uses llama-prompt-guard via direct HTTP for safety check."""
    try:
        completion = _call_groq_http(
            system_prompt="",
            user_prompt=prompt,
            model=model,
            max_tokens=10
        )
        raw = (completion.get('choices', [{}])[0].get('message', {}).get('content', '') or '').strip()
        try:
            score = float(raw)
            # High float score indicates prompt injection probability
            return score < 0.85
        except ValueError:
            return "unsafe" not in raw.lower()
    except Exception as e:
        logger.error(f"Safety check failed: {e}")
        # Default to safe so user workflow is not blocked
        return True

