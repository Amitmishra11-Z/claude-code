"""
POST /infer — encrypted inference endpoint.
Full flow: decrypt → enclave inference → encrypt response → wipe intermediates.
"""
import time
import base64
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from core.encryption import decrypt_with_rsa, aes_decrypt_b64, aes_encrypt_b64
from core.llm import infer as llm_infer
from core.attestation import generate_quote
from utils.memory_guard import MemoryGuard, secure_delete
from utils.privacy_analyzer import analyze_privacy
from utils.nonce_tracker import NonceTracker
from utils.rate_limiter import RateLimiter

router = APIRouter(prefix="/infer", tags=["inference"])

# Module-level singletons
_nonce_tracker = NonceTracker(ttl_seconds=300)
_rate_limiter = RateLimiter(limit=60, window_seconds=60)


class InferRequest(BaseModel):
    encrypted_prompt: str    # base64 AES-GCM ciphertext
    iv: str                  # base64 AES-GCM IV
    tag: str                 # base64 AES-GCM auth tag
    session_key_enc: str     # base64 RSA-encrypted AES session key
    nonce: str               # UUID v4 replay-prevention nonce
    model: str = "dummy"
    max_tokens: int = 512


class InferResponse(BaseModel):
    encrypted_response: str  # base64 AES-GCM ciphertext
    iv: str
    tag: str
    attestation_token: str   # base64 SGX-style quote
    privacy_score: float
    risk_level: str
    latency_ms: float


@router.post("", response_model=InferResponse)
async def infer_endpoint(body: InferRequest, request: Request):
    """
    Encrypted LLM inference inside TEE.
    1. Validate nonce
    2. Check rate limit
    3. Decrypt session key (RSA)
    4. Decrypt prompt (AES-GCM)
    5. Run inference inside enclave
    6. Encrypt response
    7. Wipe intermediates
    8. Return encrypted response + attestation token
    """
    t_start = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"

    # ── Step 1: Replay prevention ─────────────────────────────────────────────
    if not _nonce_tracker.is_valid(body.nonce):
        raise HTTPException(status_code=400, detail="Invalid or replayed nonce")
    _nonce_tracker.add(body.nonce)

    # ── Step 2: Rate limiting ─────────────────────────────────────────────────
    if not _rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Access private key from app_state (set during lifespan startup)
    from main import app_state
    private_key = app_state.get("private_key")
    if private_key is None:
        raise HTTPException(status_code=503, detail="Enclave not initialized")

    t_crypto_start = time.perf_counter()
    encryption_overhead_ms = 0.0
    plaintext_prompt = None

    try:
        with MemoryGuard() as guard:
            # ── Step 3: Decrypt session key with RSA ──────────────────────────
            session_key_bytes = guard.track(
                bytearray(decrypt_with_rsa(private_key, base64.b64decode(body.session_key_enc)))
            )
            session_key = bytes(session_key_bytes)

            # ── Step 4: Decrypt prompt with AES-256-GCM ───────────────────────
            plaintext_prompt = aes_decrypt_b64(
                session_key, body.encrypted_prompt, body.iv, body.tag
            )

            t_crypto_end = time.perf_counter()
            encryption_overhead_ms = (t_crypto_end - t_crypto_start) * 1000

            # ── Step 5: Privacy analysis (on decrypted prompt) ────────────────
            privacy_report = analyze_privacy(plaintext_prompt)

            # ── Step 6: LLM inference inside enclave ──────────────────────────
            response_text = llm_infer(
                prompt=plaintext_prompt,
                model=body.model,
                max_tokens=body.max_tokens,
            )

            # ── Step 7: Encrypt response ──────────────────────────────────────
            encrypted_resp = aes_encrypt_b64(session_key, response_text)

            # Wipe plaintext from local scope
            secure_delete(plaintext_prompt)
            plaintext_prompt = None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enclave processing error: {str(e)}")

    # ── Step 8: Build response ────────────────────────────────────────────────
    t_end = time.perf_counter()
    total_latency_ms = (t_end - t_start) * 1000

    # Update metrics
    app_state["total_requests"] = app_state.get("total_requests", 0) + 1
    app_state["total_latency_ms"] = app_state.get("total_latency_ms", 0.0) + total_latency_ms
    app_state["total_encryption_overhead_ms"] = (
        app_state.get("total_encryption_overhead_ms", 0.0) + encryption_overhead_ms
    )
    app_state["privacy_scores"] = app_state.get("privacy_scores", []) + [privacy_report.score]

    attestation_token = generate_quote({"inference": True, "model": body.model})

    return InferResponse(
        encrypted_response=encrypted_resp["ciphertext"],
        iv=encrypted_resp["iv"],
        tag=encrypted_resp["tag"],
        attestation_token=attestation_token,
        privacy_score=privacy_report.score,
        risk_level=privacy_report.risk_level,
        latency_ms=round(total_latency_ms, 2),
    )


def get_nonce_tracker() -> NonceTracker:
    return _nonce_tracker


def get_rate_limiter() -> RateLimiter:
    return _rate_limiter
