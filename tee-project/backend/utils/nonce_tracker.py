"""
Replay-attack prevention via nonce tracking with TTL.
# [REAL] In-memory set with timestamp; production would use Redis for distributed deployments.
"""
import time
import threading
from typing import Dict


class NonceTracker:
    """
    Tracks used nonces to prevent replay attacks.
    Nonces expire after `ttl_seconds` (default 5 minutes).
    # [REAL] Thread-safe in-process store
    """

    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._store: Dict[str, float] = {}  # nonce -> timestamp
        self._lock = threading.Lock()

    def is_valid(self, nonce: str) -> bool:
        """
        Returns True if nonce has NOT been seen before and is not expired format.
        Returns False if nonce was already used (replay attack detected).
        """
        self.cleanup_expired()
        with self._lock:
            return nonce not in self._store

    def add(self, nonce: str) -> None:
        """Record a nonce as used."""
        with self._lock:
            self._store[nonce] = time.time()

    def cleanup_expired(self) -> int:
        """Remove nonces older than TTL. Returns number removed."""
        cutoff = time.time() - self._ttl
        with self._lock:
            expired = [n for n, ts in self._store.items() if ts < cutoff]
            for n in expired:
                del self._store[n]
        return len(expired)

    @property
    def size(self) -> int:
        """Current number of tracked nonces."""
        return len(self._store)
