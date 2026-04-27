#!/usr/bin/env bash
# ============================================================
# run_dev.sh — Start the TEE backend in development mode
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Load .env if present ──────────────────────────────────────────────────────
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -o allexport
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
    set +o allexport
    echo "[env] Loaded $PROJECT_ROOT/.env"
fi

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

echo "========================================"
echo " TEE LLM Inference — Development Server"
echo "========================================"
echo ""
echo "  Backend URL : http://$HOST:$PORT"
echo "  API Docs    : http://localhost:$PORT/docs"
echo "  Health      : http://localhost:$PORT/health"
echo "  Attestation : http://localhost:$PORT/attest"
echo "  Metrics     : http://localhost:$PORT/metrics"
echo ""
echo "  LLM Backend : $([ -n "${OPENAI_API_KEY:-}" ] && echo 'OpenAI GPT' || echo 'DummyLLM (set OPENAI_API_KEY for real)')"
echo "  TEE Mode    : ${ENCLAVE_SIMULATION:-true} (simulation)"
echo ""
echo "  Press Ctrl+C to stop."
echo "========================================"
echo ""

# Activate venv if present
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Run uvicorn from the backend directory so relative imports resolve correctly
cd "$PROJECT_ROOT/backend"
exec uvicorn main:app \
    --host "$HOST" \
    --port "$PORT" \
    --reload \
    --log-level warning \
    --no-access-log
