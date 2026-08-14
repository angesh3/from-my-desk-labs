"""In-memory per-IP rate limiter for the public demo. Not a production WAF."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = max(1, limit)
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True
