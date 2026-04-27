# Privacy-Preserving LLM Inference using TEE

> **B.Tech Final Year Project** — Secure AI inference that protects user data from server-side logging, data leakage, unauthorised model training usage, and cloud/GPU access.

---

## Overview

This project implements a complete end-to-end encrypted LLM inference pipeline using a simulated Trusted Execution Environment (TEE). User prompts are **AES-256-GCM encrypted in the browser** before leaving the client, decrypted **only inside the enclave**, processed, re-encrypted, and returned — the server operator never sees plaintext.

```
User → [AES encrypt prompt] → POST /infer → [RSA unwrap key] → [AES decrypt in enclave]
                                                                    ↓
User ← [AES decrypt response] ← HTTP 200 ← [AES encrypt response] ← LLM inference
```

### Security Guarantees

| Feature | Status |
|---|---|
| End-to-end AES-256-GCM encryption | ✅ Real |
| RSA-2048-OAEP session key exchange | ✅ Real |
| Zero-logging policy (no request logs) | ✅ Real |
| Ephemeral memory (wiped after each request) | ✅ Real |
| PII detection + Privacy Score (0–100) | ✅ Real |
| Replay attack prevention (nonce tracker) | ✅ Real |
| Rate limiting (60 req/min/IP) | ✅ Real |
| Ciphertext integrity (GCM auth tag) | ✅ Real |
| TEE memory isolation | 🔶 Simulated (upgrade path in docs) |
| Remote attestation quotes | 🔶 Simulated (upgrade path in docs) |

---

## Quick Start (3 commands)

```bash
cd tee-project
bash scripts/setup.sh          # install deps, create .venv, create .env
bash scripts/run_dev.sh        # start FastAPI backend on http://localhost:8000
# Open frontend/index.html in your browser
```

---

## Prerequisites

- Python 3.11+
- Docker + Docker Compose (for containerised deployment)
- A modern browser (Chrome, Firefox, Edge — for Web Crypto API)
- Optional: `OPENAI_API_KEY` environment variable for real GPT inference

No Node.js. No npm. No build step.

---

## Manual Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Install docs dependencies (only needed for Word doc generation)
pip install -r docs/requirements.txt

# 4. Copy and edit environment file
cp .env.example .env               # edit OPENAI_API_KEY if desired

# 5. Start the backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 6. Open the dashboard
open ../frontend/index.html        # or open in browser manually
```

---

## Docker Deployment

```bash
# Build and start all services (backend + nginx)
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d

# Verify
curl http://localhost:8000/health

# Stop
docker compose -f docker/docker-compose.yml down
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(empty)* | Set to use real GPT model. Leave empty for DummyLLM. |
| `PORT` | `8000` | Port the backend listens on. |
| `HOST` | `0.0.0.0` | Bind address. |
| `ENCLAVE_SIMULATION` | `true` | Set `false` only with real SGX + Gramine. |
| `NO_LOGGING` | `true` | Documents the no-logging policy. |

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Server health check |
| `/public-key` | GET | RSA-2048 public key (PEM) |
| `/attest` | GET | Full remote attestation report |
| `/verify-quote` | POST | Verify an attestation quote |
| `/infer` | POST | Encrypted inference (main endpoint) |
| `/metrics` | GET | Runtime metrics (latency, privacy scores) |
| `/docs` | GET | Auto-generated OpenAPI documentation |

### POST /infer — Request Body

```json
{
  "encrypted_prompt": "<base64 AES-GCM ciphertext>",
  "iv":               "<base64 AES-GCM IV (12 bytes)>",
  "tag":              "<base64 AES-GCM auth tag (16 bytes)>",
  "session_key_enc":  "<base64 RSA-OAEP encrypted AES key>",
  "nonce":            "<UUID v4 replay-prevention nonce>",
  "model":            "dummy",
  "max_tokens":       512
}
```

### POST /infer — Response Body

```json
{
  "encrypted_response": "<base64 AES-GCM ciphertext>",
  "iv":                 "<base64 IV>",
  "tag":                "<base64 auth tag>",
  "attestation_token":  "<base64 simulated SGX quote>",
  "privacy_score":      97.5,
  "risk_level":         "LOW",
  "latency_ms":         12.4
}
```

---

## Running Tests

```bash
source .venv/bin/activate
cd backend
pytest ../tests/ -v

# With coverage
pytest ../tests/ --cov=. --cov-report=term-missing -v
```

---

## CLI Demo Client

```bash
source .venv/bin/activate

# Basic usage (server must be running)
python scripts/demo_client.py "Explain TEE"

# Verbose mode
python scripts/demo_client.py "Tell me about privacy" --verbose

# Custom model and token count
python scripts/demo_client.py "Hello" --model dummy --max-tokens 128
```

---

## Performance Report

```bash
# Benchmark 50 requests and generate an HTML report with charts
python eval/report_generator.py --requests 50 --out eval/report.html
open eval/report.html
```

---

## Generate Word Document

```bash
pip install -r docs/requirements.txt
python docs/generate_word_doc.py
# Output: TEE_LLM_Inference_Project_Report.docx
```

---

## Project Structure

```
tee-project/
├── backend/         FastAPI application (routers, core, utils)
├── frontend/        Single-page dashboard (HTML + CSS + JS)
├── docker/          Dockerfile and docker-compose
├── tests/           pytest test suite
├── scripts/         setup.sh, run_dev.sh, demo_client.py
├── eval/            HTML performance report generator
├── docs/            Word document generator
└── README.md        This file
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│  BROWSER  (Confidential Mode ON)                    │
│  ┌─────────────────────────────────────────────┐    │
│  │  AES-256-GCM encrypt prompt                 │    │
│  │  RSA-OAEP wrap session key                  │    │
│  │  POST /infer  (no plaintext in payload)     │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────┐
│  BACKEND HOST  (FastAPI)                            │
│  ├─ Nonce check (replay prevention)                 │
│  ├─ Rate limit  (60 req/min/IP)                     │
│  └─ RSA decrypt session key                         │
│  ┌─────────────────────────────────────────────┐    │
│  │  [TEE ENCLAVE — Simulated SGX]              │    │
│  │  ├─ AES decrypt → plaintext prompt          │    │
│  │  ├─ Privacy analysis (PII score)            │    │
│  │  ├─ LLM inference (Dummy / OpenAI)          │    │
│  │  ├─ AES encrypt response                    │    │
│  │  └─ Wipe all intermediates (MemoryGuard)    │    │
│  └─────────────────────────────────────────────┘    │
│  Return: { encrypted_response, attestation, score } │
└─────────────────────────────────────────────────────┘
```

---

## Security Notes

- **No logging**: FastAPI is configured without access log middleware. No request body is ever written to disk.
- **Ephemeral keys**: RSA key pair is generated fresh on every server startup. Session keys are generated fresh per request.
- **Memory wipe**: `MemoryGuard` overwrites all sensitive buffers with zeros on context exit.
- **Authenticated encryption**: AES-GCM auth tag rejects any ciphertext tampering before decryption.
- **Replay prevention**: UUID nonces are tracked with a 5-minute TTL.

---

## Upgrading to Real Intel SGX

See **Chapter 7** of `TEE_LLM_Inference_Project_Report.docx` for the complete step-by-step guide using Gramine-SGX or AWS Nitro Enclaves.

---

## License

MIT — use freely for educational purposes.
