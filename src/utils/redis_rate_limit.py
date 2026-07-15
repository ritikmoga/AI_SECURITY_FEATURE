"""Redis fixed-window limiter with a safe in-memory fallback."""
from __future__ import annotations

import time

from src.utils.rate_limit import InMemoryRateLimiter


class RedisRateLimiter:
    def __init__(self, redis_url: str, max_requests: int, window_seconds: int) -> None:
        import redis

        self.client = redis.Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.fallback = InMemoryRateLimiter(max_requests, window_seconds)

    def allow(self, key: str) -> tuple[bool, int]:
        bucket = int(time.time() // self.window_seconds)
        redis_key = f"scamshield:rate:{key}:{bucket}"
        try:
            pipeline = self.client.pipeline()
            pipeline.incr(redis_key)
            pipeline.expire(redis_key, self.window_seconds + 1)
            count, _ = pipeline.execute()
            if int(count) <= self.max_requests:
                return True, 0
            return False, max(1, self.client.ttl(redis_key))
        except Exception:
            return self.fallback.allow(key)
