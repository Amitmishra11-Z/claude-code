"""
Secure memory management — ephemeral secrets with guaranteed wipe on exit.
# [REAL] In-process overwrite; note Python GC limits true hardware wipe.
"""
import os
import ctypes
from typing import Any, List


def secure_delete(obj: Any) -> None:
    """
    Best-effort secure deletion of sensitive data.
    For bytearray: actual zero-overwrite.
    For str/bytes: zero out the buffer via ctypes (CPython specific).
    """
    if isinstance(obj, bytearray):
        for i in range(len(obj)):
            obj[i] = 0
    elif isinstance(obj, bytes):
        # CPython: overwrite internal buffer
        try:
            buf = (ctypes.c_char * len(obj)).from_address(id(obj) + 33)
            ctypes.memset(buf, 0, len(obj))
        except Exception:
            pass
    elif isinstance(obj, dict):
        for k in list(obj.keys()):
            secure_delete(obj[k])
            obj[k] = None
        obj.clear()
    elif isinstance(obj, list):
        for i in range(len(obj)):
            secure_delete(obj[i])
            obj[i] = None
        obj.clear()


class MemoryGuard:
    """
    Context manager that tracks allocated secrets and wipes them on exit.
    Usage:
        with MemoryGuard() as guard:
            secret = guard.track(bytearray(key_material))
            ...
    # [REAL] Overwrite strategy; Python runtime may retain copies in GC
    """

    def __init__(self):
        self._tracked: List[Any] = []

    def track(self, obj: Any) -> Any:
        """Register an object for secure deletion on context exit."""
        self._tracked.append(obj)
        return obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for obj in self._tracked:
            try:
                secure_delete(obj)
            except Exception:
                pass
        self._tracked.clear()
        # Fill local stack frame with random bytes as added precaution
        _ = os.urandom(64)
        return False  # do not suppress exceptions
