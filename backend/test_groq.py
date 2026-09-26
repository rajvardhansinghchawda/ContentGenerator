import json
import os
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def main() -> int:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("ERROR: GROQ_API_KEY is not set")
        return 1

    candidate_models = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-safeguard-20b"
    ]

    for model in candidate_models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Reply with exactly: pong"},
            ],
            "temperature": 0,
            "max_tokens": 16,
        }

        request = urlrequest.Request(
            GROQ_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            method="POST",
        )

        try:
            with urlrequest.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
                text = body["choices"][0]["message"]["content"].strip()
                print(f"[{model}] SUCCESS (200): {text}")
        except HTTPError as exc:
            try:
                error_body = exc.read().decode("utf-8")
            except Exception:
                error_body = ""
            print(f"[{model}] HTTP {exc.code}: {error_body or exc.reason}")
        except Exception as exc:
            print(f"[{model}] ERROR: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
