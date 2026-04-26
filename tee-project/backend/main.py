"""
FastAPI entrypoint for Privacy-Preserving LLM Inference TEE backend.
Privacy policy: NO request/response logging middleware.
All state is ephemeral in-memory only.
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.encryption import generate_rsa_keypair, export_public_key_pem
from core.enclave import initialize_enclave
from routers import inference, attestation, metrics

# ── Application state (ephemeral, never persisted) ────────────────────────────
app_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────────
    private_key, public_key = generate_rsa_keypair(bits=2048)
    enclave = initialize_enclave()

    app_state["private_key"] = private_key
    app_state["public_key"] = public_key
    app_state["public_key_pem"] = export_public_key_pem(public_key)
    app_state["enclave"] = enclave
    app_state["start_time"] = time.time()
    app_state["total_requests"] = 0
    app_state["total_latency_ms"] = 0.0
    app_state["total_encryption_overhead_ms"] = 0.0
    app_state["privacy_scores"] = []

    yield

    # ── Shutdown — wipe all sensitive state ───────────────────────────────────
    app_state.clear()


app = FastAPI(
    title="Privacy-Preserving LLM Inference TEE",
    version="1.0.0",
    description="B.Tech project: LLM inference inside a simulated Trusted Execution Environment",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

# ── CORS (adjust origins for production) ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NOTE: NO logging middleware — privacy policy prohibits logging user queries.

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(inference.router)
app.include_router(attestation.router)
app.include_router(metrics.router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - app_state.get("start_time", time.time()), 1),
        "enclave_active": app_state.get("enclave") is not None,
    }
