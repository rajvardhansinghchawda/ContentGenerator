"""
GroqAIAgent — Calls the Groq API and returns parsed content.
"""
import json
import logging
import time
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from django.conf import settings

logger = logging.getLogger(__name__)

FALLBACK_MODEL = 'llama-3.1-8b-instant'
GROQ_CHAT_COMPLETIONS_URL = 'https://api.groq.com/openai/v1/chat/completions'


def _call_groq_http(system_prompt: str, user_prompt: str, model: str) -> dict:
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': 0.7,
        'max_tokens': 4096,
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


def call_groq(system_prompt: str, user_prompt: str, max_retries: int = 3) -> dict:
    """
    Calls Groq API with retry logic. Returns parsed JSON dict.
    Raises ValueError if content cannot be parsed after retries.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError('GROQ_API_KEY is not configured.')

    model = settings.GROQ_MODEL
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Groq API call attempt {attempt + 1} with model {model}")

            response = _call_groq_http(system_prompt, user_prompt, model)
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
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff

        except HTTPError as e:
            try:
                err_body = e.read().decode('utf-8')
            except Exception:
                err_body = ''
            last_error = f"HTTP {e.code}: {err_body or e.reason}"

            # Cloudflare 1010 is an access-control denial (region/network/account policy),
            # and retrying will not help.
            if e.code == 403 and '1010' in last_error:
                raise PermissionError(
                    'Groq access denied (HTTP 403 / code 1010). '
                    'This is typically a region/network restriction or key/account policy block. '
                    'Use a permitted network/API key or switch provider.'
                )

            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            if attempt == 1 and model != FALLBACK_MODEL:
                model = FALLBACK_MODEL
                logger.info(f"Switching to fallback model: {FALLBACK_MODEL}")
            elif attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except URLError as e:
            last_error = f"Network error: {e.reason}"
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            # Try fallback model on second attempt
            if attempt == 1 and model != FALLBACK_MODEL:
                model = FALLBACK_MODEL
                logger.info(f"Switching to fallback model: {FALLBACK_MODEL}")
            elif attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    raise ValueError(f"Groq API failed after {max_retries} attempts. Last error: {last_error}")
