"""
GET /metrics — runtime performance and privacy metrics.
"""
import time
from fastapi import APIRouter

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics():
    """Return aggregated runtime metrics."""
    from main import app_state
    from routers.inference import get_nonce_tracker, get_rate_limiter

    total_req = app_state.get("total_requests", 0)
    total_lat = app_state.get("total_latency_ms", 0.0)
    total_enc = app_state.get("total_encryption_overhead_ms", 0.0)
    scores = app_state.get("privacy_scores", [])
    start_time = app_state.get("start_time", time.time())

    nt = get_nonce_tracker()
    rl = get_rate_limiter()

    return {
        "total_requests": total_req,
        "avg_latency_ms": round(total_lat / total_req, 2) if total_req else 0.0,
        "encryption_overhead_ms": round(total_enc / total_req, 2) if total_req else 0.0,
        "privacy_score_avg": round(sum(scores) / len(scores), 1) if scores else 100.0,
        "enclave_uptime_s": round(time.time() - start_time, 1),
        "nonce_cache_size": nt.size,
        "rate_limit_hits": rl.get_stats()["total_violations"],
        "rate_limiter": rl.get_stats(),
    }
