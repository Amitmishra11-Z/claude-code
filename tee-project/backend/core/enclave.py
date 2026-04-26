"""
Simulated TEE (Trusted Execution Environment) enclave context.
# [SIMULATED] — Real implementation would use Intel SGX + Gramine or AWS Nitro Enclaves
"""
import time
import hashlib
import secrets
import threading
from contextlib import contextmanager
from typing import Any, Dict, Optional


class EnclaveContext:
    """
    Simulates an Intel SGX-like enclave with isolated memory and audit logging.
    # [SIMULATED] In production, this would be an actual SGX enclave.
    """

    def __init__(self):
        self._isolated_memory: Dict[str, Any] = {}  # # [SIMULATED] isolated heap
        self._audit_log: list = []                   # stays inside enclave only
        self._start_time: float = time.time()
        self._lock = threading.Lock()
        self._active = False
        self._enclave_id = secrets.token_hex(16)
        # Simulated measurement (in real SGX this is a hardware hash of enclave code)
        self._mrenclave = hashlib.sha256(self._enclave_id.encode()).hexdigest()
        self._mrsigner = hashlib.sha256(b"simulated-signer-key").hexdigest()

    def enter(self):
        """Enter the enclave (acquire exclusive lock on isolated memory). # [SIMULATED]"""
        self._lock.acquire()
        self._active = True
        self._audit_log.append({"event": "enter", "ts": time.time()})

    def exit_enclave_ctx(self, exc_type=None):
        """Exit the enclave, clear isolated memory. # [SIMULATED]"""
        self._isolated_memory.clear()  # wipe transient state on exit
        self._active = False
        self._audit_log.append({"event": "exit", "ts": time.time(), "error": exc_type is not None})
        try:
            self._lock.release()
        except RuntimeError:
            pass

    @contextmanager
    def run(self):
        """Context manager for enclave execution."""
        self.enter()
        try:
            yield self
        finally:
            self.exit_enclave_ctx()

    def store(self, key: str, value: Any):
        """Store data in isolated enclave memory."""
        if not self._active:
            raise RuntimeError("Enclave not active")
        self._isolated_memory[key] = value

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from isolated enclave memory."""
        if not self._active:
            raise RuntimeError("Enclave not active")
        return self._isolated_memory.get(key)

    def get_enclave_status(self) -> dict:
        """Return current enclave status."""
        return {
            "enclave_id": self._enclave_id,
            "active": self._active,
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "mrenclave": self._mrenclave,
            "mrsigner": self._mrsigner,
            "trust_level": "SIMULATED",  # # [SIMULATED]
            "audit_entries": len(self._audit_log),
            "isolated_memory_keys": list(self._isolated_memory.keys()) if self._active else [],
        }

    @property
    def mrenclave(self) -> str:
        return self._mrenclave

    @property
    def mrsigner(self) -> str:
        return self._mrsigner

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time


# Global singleton enclave instance
_global_enclave: Optional[EnclaveContext] = None


def initialize_enclave() -> EnclaveContext:
    """Initialize the global enclave singleton."""
    global _global_enclave
    _global_enclave = EnclaveContext()
    return _global_enclave


def get_enclave() -> EnclaveContext:
    """Get the global enclave instance."""
    global _global_enclave
    if _global_enclave is None:
        _global_enclave = EnclaveContext()
    return _global_enclave
