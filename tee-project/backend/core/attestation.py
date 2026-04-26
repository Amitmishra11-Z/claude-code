"""
Simulated remote attestation.
# [SIMULATED] — Real attestation would use Intel DCAP / IAS quote verification
"""
import time
import json
import hashlib
import base64
import secrets
from typing import Optional

from .enclave import get_enclave


def generate_quote(enclave_data: dict) -> str:
    """
    Generate a simulated SGX quote.
    # [SIMULATED] Real quotes are signed by the CPU's attestation key.
    Returns base64-encoded JSON quote blob.
    """
    enclave = get_enclave()
    payload = {
        "version": 1,
        "type": "SIMULATED_SGX_QUOTE",
        "mrenclave": enclave.mrenclave,
        "mrsigner": enclave.mrsigner,
        "timestamp": time.time(),
        "nonce": secrets.token_hex(16),
        "enclave_data": enclave_data,
        "report_data": hashlib.sha256(json.dumps(enclave_data, sort_keys=True).encode()).hexdigest(),
    }
    quote_json = json.dumps(payload)
    return base64.b64encode(quote_json.encode("utf-8")).decode("utf-8")


def verify_quote(quote: str) -> bool:
    """
    Verify a simulated attestation quote.
    # [SIMULATED] Real verification checks Intel's attestation service signature.
    Returns True if the quote is structurally valid.
    """
    try:
        decoded = base64.b64decode(quote.encode("utf-8"))
        payload = json.loads(decoded)
        required_keys = {"version", "mrenclave", "mrsigner", "timestamp", "report_data"}
        if not required_keys.issubset(payload.keys()):
            return False
        # Check it's not stale (within 1 hour)
        age = time.time() - payload["timestamp"]
        if age > 3600:
            return False
        return True
    except Exception:
        return False


def get_attestation_report() -> dict:
    """
    Return a full attestation report.
    # [SIMULATED] — In production this would come from Intel's IAS or DCAP service.
    """
    enclave = get_enclave()
    status = enclave.get_enclave_status()

    platform_info = {
        "cpu_svn": secrets.token_hex(8),         # CPU Security Version Number
        "isv_svn": 1,                             # ISV Security Version Number
        "isv_prod_id": 1001,
        "attributes": {"debug": False, "mode64bit": True},
        "sgx_type": "SIMULATED",                 # # [SIMULATED]
    }

    return {
        "mrenclave": status["mrenclave"],
        "mrsigner": status["mrsigner"],
        "timestamp": time.time(),
        "platform_info": platform_info,
        "trust_level": "SIMULATED",              # # [SIMULATED]
        "enclave_uptime_s": status["uptime_seconds"],
        "quote": generate_quote({"purpose": "LLM inference", "version": "1.0"}),
        "verification_status": "QUOTE_VERIFIED_SIMULATED",
        "advisory": "This is a simulated TEE. Production deployment requires real Intel SGX hardware.",
    }
