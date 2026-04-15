import os
import redis
from dotenv import load_dotenv

# Load .env file
load_dotenv()

redis_url = os.getenv('REDIS_URL')

print(f"Testing connection to: {redis_url}")

try:
    # Connect using the URL from .env
    r = redis.from_url(redis_url)
    
    # Try a simple PING command
    response = r.ping()
    if response:
        print("[SUCCESS] Redis Ping Successful!")
        
        # Try a SET and GET
        r.set('test_key', 'Hello from EduFlow!', ex=60)
        value = r.get('test_key')
        print(f"[SUCCESS] Set/Get Test Successful! Value: {value.decode('utf-8')}")
    else:
        print("[FAILURE] Redis Ping failed (received False)")

except Exception as e:
    print(f"[ERROR] Redis Connection Failed: {str(e)}")
