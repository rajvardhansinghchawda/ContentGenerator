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
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
    'llama-3.1-70b-versatile',
    'gemma2-9b-it',
]




FALLBACK_MODEL = 'llama-3.1-8b-instant'
GROQ_CHAT_COMPLETIONS_URL = 'https://api.groq.com/openai/v1/chat/completions'


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


def call_groq(system_prompt: str, user_prompt: str, max_retries: int = 5, preferred_model: str = None, max_tokens: int = 3500) -> dict:
    """
    Calls Groq API with Model Rotation and retry logic.
    If a 429 Rate Limit hit, switches to the next available model in the pool.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError('GROQ_API_KEY is not configured.')

    # Determine model order: preferred first, then the rest of the pool
    pool = list(DEFAULT_MODEL_POOL)
    if preferred_model and preferred_model in pool:
        pool.remove(preferred_model)
        pool = [preferred_model] + pool
    elif preferred_model:
        pool = [preferred_model] + pool

    current_model_idx = 0
    last_error = None
    
    for attempt in range(max_retries):
        model = pool[current_model_idx % len(pool)]
        try:
            logger.info(f"Groq API call attempt {attempt + 1} using model: {model}")

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
            if attempt < max_retries - 1:
                time.sleep(2)

        except HTTPError as e:
            try:
                err_body = e.read().decode('utf-8')
            except Exception:
                err_body = ''
            last_error = f"HTTP {e.code}: {err_body or e.reason}"

            if e.code == 403 and '1010' in last_error:
                raise PermissionError('Groq access denied (HTTP 403 / code 1010). Check region/network.')

            logger.warning(f"Attempt {attempt + 1} failed with {model}: {last_error}")
            
            # Handle rate limit by ROTATING models
            if e.code == 429:
                current_model_idx += 1
                next_model = pool[current_model_idx % len(pool)]
                logger.info(f"Rate limit hit on {model}. Rotating to {next_model}...")
                time.sleep(2) # Short wait before trying next model
            elif attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1} failed with {model}: {last_error}")
            if attempt < max_retries - 1:
                current_model_idx += 1 # Try next model anyway for stability
                time.sleep(2)
    
    raise ValueError(f"Groq API failed after {max_retries} attempts with rotation. Last error: {last_error}")


def verify_prompt_safety(text: str) -> bool:
    """Uses llama-prompt-guard-2-22m for a safe check."""
    if not settings.GROQ_API_KEY:
        return True
    try:
        response = _call_groq_http(
            system_prompt="You are a safety classifier.", 
            user_prompt=text, 
            model="llama-prompt-guard-2-22m",
            max_tokens=10
        )
        classification = (response.get('choices', [{}])[0].get('message', {}).get('content', '') or '').strip().lower()
        logger.info(f"Safety check result: {classification}")
        return "malicious" not in classification
    except Exception as e:
        logger.error(f"Safety check failed: {e}")
        return True
