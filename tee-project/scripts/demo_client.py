#!/usr/bin/env python3
"""
demo_client.py — End-to-end demo of the TEE LLM inference pipeline.

Demonstrates:
  1. Fetch RSA public key from the attestation endpoint
  2. Generate an AES-256 session key
  3. Encrypt the prompt using AES-256-GCM
  4. Encrypt the session key using RSA-OAEP
  5. Send encrypted payload to /infer
  6. Decrypt the response
  7. Print timing, privacy score, and attestation info

# [REAL] All cryptography uses pycryptodome — real primitives
# Run from project root: python scripts/demo_client.py
"""
import os
import sys
import time
import json
import base64
import uuid
import argparse

# ── Allow running without venv if pycryptodome/requests are installed globally ─
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Random import get_random_bytes
    import httpx
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install pycryptodome httpx")
    sys.exit(1)

BASE_URL = os.environ.get("TEE_BASE_URL", "http://localhost:8000")


# ── Crypto helpers ─────────────────────────────────────────────────────────────

def generate_session_key() -> bytes:
    """Generate 256-bit AES session key. # [REAL]"""
    return get_random_bytes(32)


def aes_encrypt(key: bytes, plaintext: str) -> dict:
    """AES-256-GCM encrypt. Returns dict with base64 fields. # [REAL]"""
    iv = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    return {
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "iv":         base64.b64encode(iv).decode(),
        "tag":        base64.b64encode(tag).decode(),
    }


def aes_decrypt(key: bytes, ciphertext_b64: str, iv_b64: str, tag_b64: str) -> str:
    """AES-256-GCM decrypt. # [REAL]"""
    ciphertext = base64.b64decode(ciphertext_b64)
    iv         = base64.b64decode(iv_b64)
    tag        = base64.b64decode(tag_b64)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")


def rsa_encrypt_session_key(public_key_pem: str, session_key: bytes) -> str:
    """Encrypt session key with server's RSA public key. # [REAL]"""
    pub_key = RSA.import_key(public_key_pem.encode("utf-8"))
    cipher  = PKCS1_OAEP.new(pub_key)
    return base64.b64encode(cipher.encrypt(session_key)).decode()


# ── Demo steps ─────────────────────────────────────────────────────────────────

def step(n: int, title: str):
    print(f"\n{'─'*55}")
    print(f"  Step {n}: {title}")
    print(f"{'─'*55}")


def run_demo(prompt: str, model: str = "dummy", max_tokens: int = 256, verbose: bool = False):
    client = httpx.Client(base_url=BASE_URL, timeout=30)

    print("\n" + "═"*55)
    print("  TEE LLM Inference — End-to-End Demo Client")
    print("═"*55)
    print(f"  Server  : {BASE_URL}")
    print(f"  Prompt  : {prompt!r}")
    print(f"  Model   : {model}")

    # ── Step 1: Check server health ────────────────────────────────────────────
    step(1, "Check server health")
    t0 = time.perf_counter()
    health = client.get("/health").json()
    print(f"  Status        : {health['status']}")
    print(f"  Uptime        : {health['uptime_seconds']}s")
    print(f"  Enclave active: {health['enclave_active']}")

    # ── Step 2: Fetch RSA public key via /attest ───────────────────────────────
    step(2, "Fetch server RSA public key from /public-key")
    attest_resp = client.get("/public-key")
    attest_resp.raise_for_status()
    public_key_pem = attest_resp.json()["public_key_pem"]
    key_preview = public_key_pem.split("\n")[1][:40] + "…"
    print(f"  RSA-2048 PEM  : {key_preview}")

    # ── Step 3: Generate AES session key ──────────────────────────────────────
    step(3, "Generate AES-256-GCM session key (client-side)")
    session_key = generate_session_key()
    print(f"  Session key   : {session_key.hex()[:16]}…  (32 bytes, not transmitted in plaintext)")

    # ── Step 4: Encrypt prompt with AES-GCM ──────────────────────────────────
    step(4, "Encrypt prompt with AES-256-GCM (client-side)")
    t_enc_start = time.perf_counter()
    enc_prompt = aes_encrypt(session_key, prompt)
    t_enc_end   = time.perf_counter()
    enc_overhead_ms = (t_enc_end - t_enc_start) * 1000
    print(f"  Ciphertext    : {enc_prompt['ciphertext'][:32]}…")
    print(f"  IV            : {enc_prompt['iv']}")
    print(f"  Tag           : {enc_prompt['tag']}")
    print(f"  Encrypt time  : {enc_overhead_ms:.2f} ms")

    # ── Step 5: Encrypt session key with RSA ──────────────────────────────────
    step(5, "Encrypt session key with server RSA-2048 public key")
    t_rsa_start = time.perf_counter()
    enc_session_key = rsa_encrypt_session_key(public_key_pem, session_key)
    t_rsa_end = time.perf_counter()
    rsa_overhead_ms = (t_rsa_end - t_rsa_start) * 1000
    print(f"  Encrypted key : {enc_session_key[:32]}…")
    print(f"  RSA-OAEP time : {rsa_overhead_ms:.2f} ms")

    # ── Step 6: Send encrypted payload to /infer ──────────────────────────────
    step(6, "Send encrypted request to POST /infer")
    nonce = str(uuid.uuid4())
    payload = {
        "encrypted_prompt": enc_prompt["ciphertext"],
        "iv":               enc_prompt["iv"],
        "tag":              enc_prompt["tag"],
        "session_key_enc":  enc_session_key,
        "nonce":            nonce,
        "model":            model,
        "max_tokens":       max_tokens,
    }
    if verbose:
        print("  Payload (no plaintext exposed):")
        for k, v in payload.items():
            display = str(v)
            print(f"    {k:20s}: {display[:50]}{'…' if len(display) > 50 else ''}")

    t_req_start = time.perf_counter()
    resp = client.post("/infer", json=payload)
    t_req_end = time.perf_counter()
    network_ms = (t_req_end - t_req_start) * 1000

    if resp.status_code != 200:
        print(f"  ERROR {resp.status_code}: {resp.text}")
        sys.exit(1)

    result = resp.json()
    print(f"  HTTP status   : {resp.status_code} OK")
    print(f"  Network RTT   : {network_ms:.1f} ms")
    print(f"  Server latency: {result['latency_ms']} ms")

    # ── Step 7: Decrypt response ───────────────────────────────────────────────
    step(7, "Decrypt response (client-side, AES-256-GCM)")
    t_dec_start = time.perf_counter()
    plaintext_response = aes_decrypt(
        session_key,
        result["encrypted_response"],
        result["iv"],
        result["tag"],
    )
    t_dec_end = time.perf_counter()
    dec_overhead_ms = (t_dec_end - t_dec_start) * 1000
    print(f"  Decrypt time  : {dec_overhead_ms:.2f} ms")

    # ── Step 8: Show results ───────────────────────────────────────────────────
    step(8, "Results")
    print(f"\n  Decrypted response:\n  {'─'*50}")
    # Word-wrap at 50 chars
    words = plaintext_response.split()
    line  = "  "
    for word in words:
        if len(line) + len(word) + 1 > 53:
            print(line)
            line = "  " + word
        else:
            line += (" " if line != "  " else "") + word
    if line.strip():
        print(line)
    print(f"  {'─'*50}")

    print(f"\n  Privacy score : {result['privacy_score']}/100 ({result['risk_level']} risk)")
    print(f"  Attestation   : {result['attestation_token'][:40]}…  [SIMULATED SGX quote]")

    # ── Summary ───────────────────────────────────────────────────────────────
    total_client_ms = (
        enc_overhead_ms + rsa_overhead_ms + network_ms + dec_overhead_ms
    )
    print("\n" + "═"*55)
    print("  Performance Summary")
    print("═"*55)
    print(f"  Client AES encrypt  : {enc_overhead_ms:.2f} ms")
    print(f"  Client RSA encrypt  : {rsa_overhead_ms:.2f} ms")
    print(f"  Network RTT         : {network_ms:.1f} ms")
    print(f"  Server total        : {result['latency_ms']} ms")
    print(f"  Client AES decrypt  : {dec_overhead_ms:.2f} ms")
    print(f"  ─────────────────────────────────────────")
    print(f"  Total client time   : {total_client_ms:.1f} ms")
    print("═"*55)
    print("\n  Demo complete. Your prompt was NEVER transmitted in plaintext.\n")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TEE LLM Inference — end-to-end demo client"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Explain TEE",
        help="Prompt to send (default: 'Explain TEE')",
    )
    parser.add_argument(
        "--model",
        default="dummy",
        help="LLM model to use (default: dummy)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=256,
        dest="max_tokens",
        help="Max tokens in response (default: 256)",
    )
    parser.add_argument(
        "--url",
        default=BASE_URL,
        help=f"Backend base URL (default: {BASE_URL})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full request payload",
    )
    args = parser.parse_args()
    BASE_URL = args.url
    run_demo(args.prompt, model=args.model, max_tokens=args.max_tokens, verbose=args.verbose)
