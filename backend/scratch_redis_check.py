import os
import redis
import environ
from pathlib import Path

# Load env
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

redis_url = env('REDIS_URL')
print(f"Connecting to: {redis_url[:20]}...")

try:
    r = redis.from_url(redis_url)
    ping = r.ping()
    if ping:
        print("SUCCESS: Redis Connection Successful!")
    else:
        print("FAILED: Redis Ping failed.")
except Exception as e:
    print(f"FAILED: Error: {e}")
