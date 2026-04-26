"""
Per-IP sliding window rate limiter.
# [REAL] In-memory; production would use Redis + token bucket.
"""
import time
import threading
from collections import deque
from typing import Dict, Deque


class RateLimiter:
    """
    Sliding window rate limiter: max `limit` requests per `window_seconds`.
    Default: 60 requests per 60 seconds per IP.
    # [REAL] Thread-safe in-process implementation
    """

    def __init__(self, limit: int = 60, window_seconds: int = 60):
        self._limit = limit
        self._window = window_seconds
        self._requests: Dict[str, Deque[float]] = {}
        self._hits: int = 0  # total rate-limit violations
        self._lock = threading.Lock()

    def is_allowed(self, ip: str) -> bool:
        """Check if this IP is within rate limit. Thread-safe."""
        now = time.time()
        cutoff = now - self._window

        with self._lock:
            if ip not in self._requests:
                self._requests[ip] = deque()

            dq = self._requests[ip]
            # Remove timestamps outside window
            while dq and dq[0] < cutoff:
                dq.popleft()

            if len(dq) >= self._limit:
                self._hits += 1
                return False

            dq.append(now)
            return True

    def get_stats(self) -> dict:
        """Return rate limiter statistics."""
        with self._lock:
            total_ips = len(self._requests)
            total_tracked = sum(len(dq) for dq in self._requests.values())
        return {
            "tracked_ips": total_ips,
            "active_requests_window": total_tracked,
            "limit_per_window": self._limit,
            "window_seconds": self._window,
            "total_violations": self._hits,
        }
