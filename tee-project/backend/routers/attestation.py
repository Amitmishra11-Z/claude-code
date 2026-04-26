"""
GET /attest  — full attestation report
GET /public-key — RSA public key in PEM format
"""
from fastapi import APIRouter, HTTPException
from fastapi import Request

from core.attestation import get_attestation_report, verify_quote

router = APIRouter(tags=["attestation"])


@router.get("/attest")
async def attest(request: Request):
    """Return the full remote attestation report for this enclave instance."""
    report = get_attestation_report()
    return report


@router.get("/public-key")
async def public_key(request: Request):
    """Return the RSA-2048 public key in PEM format for client-side session key encryption."""
    from main import app_state
    pem = app_state.get("public_key_pem")
    if not pem:
        raise HTTPException(status_code=503, detail="Key not yet generated")
    return {"public_key_pem": pem, "algorithm": "RSA-2048-OAEP", "usage": "session_key_encryption"}


@router.post("/verify-quote")
async def verify_quote_endpoint(payload: dict):
    """Verify a previously issued attestation quote."""
    quote = payload.get("quote", "")
    valid = verify_quote(quote)
    return {"valid": valid, "message": "Quote verified (simulated)" if valid else "Invalid quote"}
