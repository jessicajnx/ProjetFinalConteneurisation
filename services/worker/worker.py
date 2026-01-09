import os
import json
import time
import redis


def get_redis_client() -> redis.Redis:
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    return redis.Redis(host=host, port=port, db=db, decode_responses=True)


def main():
    r = get_redis_client()
    print("Worker started. Processing jobs: text to UPPERCASE...")
    print(f"Connecting to Redis at {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}")
    
    while True:
        try:
            item = r.blpop(["jobs"], timeout=5)
            if not item:
                continue
            _, payload_str = item
            payload = json.loads(payload_str)
            job_id = payload["id"]
            text = payload["text"]

            status_key = f"job:{job_id}:status"
            result_key = f"job:{job_id}:result"

            r.set(status_key, "processing", ex=3600)
            print(f"Processing job {job_id}: '{text}'")

            # Simple uppercase transformation
            time.sleep(0.5)
            result = text.upper()

            r.set(result_key, result, ex=3600)
            r.set(status_key, "done", ex=3600)
            print(f"Completed job {job_id}: '{text}' -> '{result}'")
        except Exception as e:
            print(f"Worker error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)


if __name__ == "__main__":
    main()
