"""Token-bucket rate limiter backed by Redis.

How a token bucket works (easy to explain in interviews):
  - Each user gets a bucket that holds up to LIMIT tokens.
  - Every request costs 1 token.
  - Tokens refill at a fixed rate (LIMIT per WINDOW seconds).
  - If the bucket is empty the request is rejected with 429.

Why Redis and not in-memory?
  - In-memory state is lost on restart and doesn't work across multiple
    server instances. Redis is shared, persistent, and fast enough.
"""

import time

import redis

from app.config import REDIS_URL

LIMIT = 20        # max requests
WINDOW = 60       # per 60 seconds

_redis = redis.from_url(REDIS_URL, decode_responses=True)


def is_rate_limited(user_id: str) -> bool:
    """Return True if the user has exceeded their request quota."""
    key = f"rate:{user_id}"
    now = time.time()
    window_start = now - WINDOW

    pipe = _redis.pipeline()
    # Remove timestamps older than the current window.
    pipe.zremrangebyscore(key, 0, window_start)
    # Count how many requests remain in the window.
    pipe.zcard(key)
    # Record this request.
    pipe.zadd(key, {str(now): now})
    # Expire the key after the window so Redis doesn't fill up.
    pipe.expire(key, WINDOW)
    _, count, *_ = pipe.execute()

    return count >= LIMIT