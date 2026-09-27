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
                {"role": "system", "content": "You are a helpful assistant. Reply with only valid JSON: {\"status\": \"ok\", \"message\": \"pong\"}"},
                {"role": "user", "content": "Ping"},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 120,
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
                choice = body["choices"][0]["message"]
                text = choice.get("content", "").strip()
                tokens = body.get("usage", {}).get("total_tokens")
                print(f"[{model}] SUCCESS (200) [tokens: {tokens}]: {text}")
        except HTTPError as exc:
            try:
                error_body = exc.read().decode("utf-8")
            except Exception:
                error_body = ""
            print(f"[{model}] HTTP {exc.code}: {error_body or exc.reason}")
        except Exception as exc:
            print(f"[{model}] ERROR: {exc}")

    # Test Prompt Guard Safety Model
    safety_model = "meta-llama/llama-prompt-guard-2-86m"
    safety_payload = {
        "model": safety_model,
        "messages": [{"role": "user", "content": "What is photosynthesis?"}],
        "max_tokens": 10,
    }
    safety_req = urlrequest.Request(
        GROQ_URL,
        data=json.dumps(safety_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(safety_req, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
            score = body["choices"][0]["message"].get("content", "").strip()
            print(f"[{safety_model}] SUCCESS (200) -> Injection Score: {score} (Safe: {float(score) < 0.85})")
    except Exception as exc:
        print(f"[{safety_model}] FAILED: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
