#!/usr/bin/env bash
# ============================================================
# setup.sh — One-time environment setup for TEE LLM project
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================"
echo " TEE LLM Inference — Project Setup"
echo "========================================"

# ── 1. Check Python version ───────────────────────────────────────────────────
echo ""
echo "[1/6] Checking Python version..."
PYTHON=$(command -v python3 || command -v python || true)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.11+ is required. Install from https://www.python.org/"
    exit 1
fi
PYVER=$("$PYTHON" -c 'import sys; print(sys.version_info[:2])')
echo "      Found: $($PYTHON --version)  ($PYVER)"

# ── 2. Create virtualenv ──────────────────────────────────────────────────────
echo ""
echo "[2/6] Creating virtual environment at $PROJECT_ROOT/.venv ..."
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    "$PYTHON" -m venv "$PROJECT_ROOT/.venv"
    echo "      Created."
else
    echo "      Already exists — skipping."
fi

# Activate
source "$PROJECT_ROOT/.venv/bin/activate"

# ── 3. Upgrade pip ────────────────────────────────────────────────────────────
echo ""
echo "[3/6] Upgrading pip..."
pip install --quiet --upgrade pip

# ── 4. Install backend dependencies ──────────────────────────────────────────
echo ""
echo "[4/6] Installing backend dependencies..."
pip install --quiet -r "$PROJECT_ROOT/backend/requirements.txt"
echo "      Done."

# ── 5. Install docs dependencies (for Word doc generation) ───────────────────
echo ""
echo "[5/6] Installing docs dependencies (python-docx)..."
pip install --quiet -r "$PROJECT_ROOT/docs/requirements.txt"
echo "      Done."

# ── 6. Create .env from example ──────────────────────────────────────────────
echo ""
echo "[6/6] Creating .env file..."
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    cat > "$PROJECT_ROOT/.env" << 'EOF'
# ── TEE LLM Inference Environment Variables ──────────────────────────────────
# Set OPENAI_API_KEY to use real GPT model instead of dummy LLM
OPENAI_API_KEY=

# Server settings
PORT=8000
HOST=0.0.0.0

# TEE settings
ENCLAVE_SIMULATION=true   # Set to false when using real Intel SGX hardware
NO_LOGGING=true           # Enforce no-logging policy
EOF
    echo "      Created .env — edit OPENAI_API_KEY to use real LLM."
else
    echo "      .env already exists — skipping."
fi

echo ""
echo "========================================"
echo " Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Activate venv:    source .venv/bin/activate"
echo "  2. Start server:     bash scripts/run_dev.sh"
echo "  3. Open dashboard:   open frontend/index.html"
echo "  4. Demo client:      python scripts/demo_client.py"
echo "  5. Run tests:        cd backend && pytest ../tests/ -v"
echo "  6. Generate docs:    python docs/generate_word_doc.py"
echo ""
