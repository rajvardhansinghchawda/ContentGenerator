import os
import django
import logging

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from ai_engine.groq_client import call_groq, verify_prompt_safety

logging.basicConfig(level=logging.INFO)

def run_test():
    print("--- Running AI Diagnostics ---")
    
    # 1. Test Safety Check
    print("Testing Safety Check (llama-prompt-guard)...")
    try:
        is_safe = verify_prompt_safety("Is photosynthesis a chemical process?")
        print(f"Safety Check Success: Responded (Is Safe: {is_safe})")
    except Exception as e:
        print(f"Safety Check FAILED: {e}")

    # 2. Test Main Model
    print("\nTesting Main Model (llama-3.3-70b-versatile)...")
    try:
        res = call_groq(
            "You are a helpful assistant.", 
            "Say 'EduFlow is Ready' in JSON format: {\"message\": \"...\"}",
            preferred_model='llama-3.3-70b-versatile',
            max_tokens=100
        )
        print(f"Main Model Success: {res['content']}")
    except Exception as e:
        print(f"Main Model FAILED: {e}")

if __name__ == "__main__":
    run_test()
