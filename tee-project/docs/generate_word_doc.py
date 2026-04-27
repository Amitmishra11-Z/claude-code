#!/usr/bin/env python3
"""
generate_word_doc.py
====================
Generates a complete, publication-ready Word document (.docx) for the
"Privacy-Preserving LLM Inference using TEE" B.Tech final-year project.

Chapters covered:
  1  Introduction
  2  System Architecture
  3  Technology Stack
  4  Folder Structure
  5  Backend Implementation
  6  Encryption Deep Dive
  7  TEE / Enclave Simulation
  8  Frontend Implementation
  9  Docker Deployment
  10 Testing
  11 Performance Evaluation
  12 Security Evaluation
  13 Privacy Score Feature
  14 Confidential Mode
  15 Future Improvements
  Appendix A – README
  Appendix B – Full Source Code Listing

Usage:
    pip install python-docx
    python docs/generate_word_doc.py

Output:
    TEE_LLM_Inference_Project_Report.docx  (written to project root)
"""
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("ERROR: python-docx not installed.\n  pip install python-docx")
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUT_FILE     = PROJECT_ROOT / "TEE_LLM_Inference_Project_Report.docx"


# ── Document builder helpers ───────────────────────────────────────────────────

def new_doc() -> Document:
    doc = Document()
    # Set page margins (2.5 cm on all sides)
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.5)
    return doc


def add_page_break(doc: Document):
    doc.add_page_break()


def heading1(doc: Document, text: str):
    p = doc.add_heading(text, level=1)
    run = p.runs[0] if p.runs else p.add_run(text)
    run.font.color.rgb = RGBColor(0x1e, 0x3a, 0x8a)   # dark blue
    return p


def heading2(doc: Document, text: str):
    p = doc.add_heading(text, level=2)
    run = p.runs[0] if p.runs else p.add_run(text)
    run.font.color.rgb = RGBColor(0x1d, 0x4e, 0xd8)
    return p


def heading3(doc: Document, text: str):
    p = doc.add_heading(text, level=3)
    return p


def body(doc: Document, text: str):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(8)
    return p


def bullet(doc: Document, text: str, level: int = 0):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.25 * (level + 1))
    return p


def code_block(doc: Document, code: str):
    """Add a code block with monospace font on a light-gray background."""
    for line in code.split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after  = Pt(0)
        # Shade background gray
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"),   "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"),  "F3F4F6")
        pPr.append(shd)
        run = p.add_run(line if line else " ")
        run.font.name = "Courier New"
        run.font.size = Pt(8.5)
    # Small spacing after code block
    doc.add_paragraph()


def add_table(doc: Document, headers: list, rows: list):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.bold = True
        run.font.size = Pt(9)
        # Blue header background
        tc = hdr_cells[i]._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"),   "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"),  "DBEAFE")
        tcPr.append(shd)
    # Data rows
    for ri, row_data in enumerate(rows):
        cells = table.rows[ri + 1].cells
        for ci, val in enumerate(row_data):
            cells[ci].text = str(val)
            cells[ci].paragraphs[0].runs[0].font.size = Pt(9)
    doc.add_paragraph()


def add_footer_page_numbers(doc: Document):
    """Add page numbers to the footer of every section."""
    for section in doc.sections:
        footer = section.footer
        para = footer.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()
        # Insert PAGE field
        fld_begin = OxmlElement("w:fldChar")
        fld_begin.set(qn("w:fldCharType"), "begin")
        run._r.append(fld_begin)
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = " PAGE "
        run._r.append(instr)
        fld_end = OxmlElement("w:fldChar")
        fld_end.set(qn("w:fldCharType"), "end")
        run._r.append(fld_end)
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x6b, 0x72, 0x80)


def read_source(rel_path: str) -> str:
    """Read a project source file. Return placeholder if missing."""
    full = PROJECT_ROOT / rel_path
    if full.exists():
        return full.read_text(encoding="utf-8")
    return f"# File not found: {rel_path}\n"


# ══════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ══════════════════════════════════════════════════════════════════════════════

def build_title_page(doc: Document):
    # University / Institution
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING")
    run.bold = True
    run.font.size = Pt(13)

    doc.add_paragraph()
    doc.add_paragraph()

    # Project title
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Privacy-Preserving LLM Inference\nusing Trusted Execution Environments (TEE)")
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = RGBColor(0x1e, 0x3a, 0x8a)

    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("B.Tech Final Year Project Report")
    run.italic = True
    run.font.size = Pt(14)

    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()

    # Details table
    table = doc.add_table(rows=4, cols=2)
    data = [
        ("Report Date",   datetime.now().strftime("%B %Y")),
        ("Course",        "B.Tech Computer Science & Engineering"),
        ("Domain",        "Cybersecurity / AI Systems"),
        ("Stack",         "Python · FastAPI · Docker · pycryptodome"),
    ]
    for ri, (label, value) in enumerate(data):
        cells = table.rows[ri].cells
        cells[0].text = label
        cells[1].text = value
        for cell in cells:
            cell.paragraphs[0].runs[0].font.size = Pt(11)
        cells[0].paragraphs[0].runs[0].bold = True

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS (placeholder — Word updates on open)
# ══════════════════════════════════════════════════════════════════════════════

def build_toc(doc: Document):
    heading1(doc, "Table of Contents")
    body(doc, '(Right-click this field in Microsoft Word and select "Update Field" to populate the table of contents automatically.)')

    # Insert TOC field
    p = doc.add_paragraph()
    run = p.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_begin)

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = r' TOC \o "1-3" \h \z \u '
    run._r.append(instr)

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_end)

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 1 — Introduction
# ══════════════════════════════════════════════════════════════════════════════

def ch1_introduction(doc: Document):
    heading1(doc, "Chapter 1: Introduction")

    heading2(doc, "1.1 Background and Motivation")
    body(doc,
        "Large Language Models (LLMs) such as GPT-4, LLaMA, and Mistral have transformed how "
        "humans interact with software. However, deploying LLMs in cloud environments introduces "
        "a fundamental privacy risk: every query a user types — potentially containing medical "
        "history, financial data, personal secrets, or business-sensitive information — is sent "
        "in plaintext to a remote server."
    )
    body(doc,
        "The cloud provider, model operator, infrastructure engineers, and potentially malicious "
        "insiders can all read, log, and even re-use that data for model training without the "
        "user's knowledge. This project addresses that threat by combining three technologies:"
    )
    for item in [
        "End-to-end encryption (AES-256-GCM + RSA-2048) so the prompt is never transmitted in plaintext.",
        "A Trusted Execution Environment (TEE) — a hardware-isolated CPU enclave — where inference "
        "runs in encrypted memory inaccessible to the host OS, hypervisor, or cloud provider.",
        "Remote attestation, which lets a client cryptographically verify it is talking to a genuine, "
        "unmodified enclave before sending any data.",
    ]:
        bullet(doc, item)

    heading2(doc, "1.2 Problem Statement")
    body(doc,
        "Existing LLM inference services — whether cloud APIs or self-hosted models — expose user "
        "prompts to at least one untrusted party (the server operator). This is unacceptable for "
        "use cases such as:"
    )
    for item in [
        "Medical diagnosis assistance (HIPAA-protected data)",
        "Legal document drafting (attorney-client privileged information)",
        "Financial planning (personally identifiable financial data)",
        "Enterprise IP: internal code review, product strategy queries",
    ]:
        bullet(doc, item)

    heading2(doc, "1.3 Project Goals")
    body(doc, "This project achieves the following goals:")
    goals = [
        ("G1", "End-to-end encryption", "User prompts are AES-256-GCM encrypted on the client and decrypted only inside the enclave."),
        ("G2", "Zero-logging policy",   "No request body, plaintext prompt, or response is written to any log file."),
        ("G3", "Ephemeral memory",      "All sensitive data is wiped from memory immediately after each inference call."),
        ("G4", "Remote attestation",    "Clients can verify enclave authenticity before trusting it with data."),
        ("G5", "Privacy scoring",       "Each request is analysed for PII (email, SSN, phone, etc.) and scored 0–100."),
        ("G6", "Confidential mode UI",  "A toggle in the dashboard signals when all security guarantees are active."),
    ]
    add_table(doc, ["ID", "Goal", "Description"], goals)

    heading2(doc, "1.4 Scope")
    body(doc,
        "This implementation is a complete, working prototype using a simulated TEE (the enclave "
        "is implemented in software inside the Python process). Sections 7.3 and Chapter 15 explain "
        "how to replace the simulation with real Intel SGX hardware using Gramine or Occlum."
    )

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 2 — System Architecture
# ══════════════════════════════════════════════════════════════════════════════

def ch2_architecture(doc: Document):
    heading1(doc, "Chapter 2: System Architecture")

    heading2(doc, "2.1 High-Level Component View")
    body(doc,
        "The system is split into three trust zones: the untrusted client network, the "
        "partially trusted backend host, and the fully trusted enclave:"
    )

    ascii_arch = """
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT BROWSER                                 │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Dashboard UI  (HTML + Vanilla JS + Web Crypto API)                    │ │
│  │                                                                        │ │
│  │  1. Generate AES-256 session key  (Web Crypto: generateKey)            │ │
│  │  2. Encrypt prompt with AES-GCM   (Web Crypto: encrypt)                │ │
│  │  3. Encrypt session key with RSA  (Web Crypto: wrapKey / RSA-OAEP)     │ │
│  │  4. POST /infer  { encrypted_prompt, session_key_enc, nonce, iv, tag } │ │
│  │  5. Receive encrypted response, decrypt locally                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │  HTTPS / TLS  (plaintext NEVER exposed)
┌─────────────────────────────▼───────────────────────────────────────────────┐
│                         BACKEND HOST  (FastAPI / Uvicorn)                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  POST /infer  router                                                │   │
│  │  ├─ Validate nonce (NonceTracker — replay prevention)               │   │
│  │  ├─ Check rate limit (RateLimiter — 60 req/min/IP)                  │   │
│  │  └─ Decrypt session key (RSA-OAEP, private key lives in enclave)    │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │  Enter enclave boundary                  │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │  [TEE ENCLAVE — Simulated Intel SGX]                                │   │
│  │                                                                     │   │
│  │  ├─ AES-GCM decrypt prompt  (session key)                           │   │
│  │  ├─ Privacy analysis  (PII detection, privacy score)                │   │
│  │  ├─ LLM inference  (DummyLLM or OpenAI GPT)                         │   │
│  │  ├─ AES-GCM encrypt response                                        │   │
│  │  └─ Wipe all intermediate data  (MemoryGuard)                       │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │  Encrypted response only                 │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │  Return: { encrypted_response, iv, tag, attestation_token,          │   │
│  │           privacy_score, risk_level, latency_ms }                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
"""
    code_block(doc, ascii_arch.strip())

    heading2(doc, "2.2 Data Flow (Step-by-Step)")
    steps = [
        ("1",  "Client startup",          "On page load, the dashboard fetches the server's RSA-2048 public key from GET /public-key."),
        ("2",  "Key generation",          "For each request, the client generates a fresh 256-bit AES session key using Web Crypto API."),
        ("3",  "Prompt encryption",       "The plaintext prompt is encrypted with AES-256-GCM, producing ciphertext + IV + auth tag."),
        ("4",  "Session key wrapping",    "The AES session key is encrypted (wrapped) with the server's RSA-2048 public key using OAEP padding."),
        ("5",  "Nonce generation",        "A UUID v4 nonce is generated to prevent replay attacks."),
        ("6",  "POST /infer",             "The encrypted payload (no plaintext) is sent to the server over HTTPS."),
        ("7",  "Server: nonce check",     "Server rejects duplicate nonces (TTL: 5 min). If valid, the nonce is recorded."),
        ("8",  "Server: rate limit",      "60 requests/minute per IP enforced. Excess requests receive HTTP 429."),
        ("9",  "Server: RSA decrypt",     "Server decrypts the session key using its RSA-2048 private key (inside enclave)."),
        ("10", "Server: AES decrypt",     "Prompt decrypted with AES-256-GCM. Auth tag verified — any tampering raises an exception."),
        ("11", "Server: inference",       "LLM inference runs inside the enclave context. Memory wiped on context exit."),
        ("12", "Server: AES encrypt",     "Response encrypted with the same session key. New random IV generated."),
        ("13", "Memory wipe",             "MemoryGuard overwrites all intermediate secrets (session key, plaintext)."),
        ("14", "Response transmission",   "Encrypted response + attestation token + privacy score returned to client."),
        ("15", "Client: AES decrypt",     "Client decrypts response using the session key it holds locally."),
        ("16", "Session key discarded",   "Session key is discarded after decryption. Never stored persistently."),
    ]
    add_table(doc, ["Step", "Actor", "Action"], steps)

    heading2(doc, "2.3 Security Boundaries")
    body(doc,
        "The key insight is that the RSA private key and all decrypted data exist only inside "
        "the enclave memory. The host OS, container runtime, cloud hypervisor, and the model "
        "operator never see the plaintext — even if they have full root access to the machine."
    )
    body(doc,
        "In the hardware TEE scenario (Intel SGX), this guarantee is enforced by the CPU itself. "
        "In this simulation, the guarantee is a software contract — suitable for a student project "
        "and for demonstrating the architecture."
    )

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 3 — Technology Stack
# ══════════════════════════════════════════════════════════════════════════════

def ch3_tech_stack(doc: Document):
    heading1(doc, "Chapter 3: Technology Stack")

    tech = [
        ("Python 3.11",       "Backend runtime",   "Stable, widely supported, excellent ecosystem for crypto and AI."),
        ("FastAPI 0.111",     "REST API framework","Async, high-performance, auto-generates OpenAPI docs. Built on Starlette + Pydantic."),
        ("Uvicorn",           "ASGI server",       "Production-grade async web server. Supports hot reload in development."),
        ("pycryptodome 3.20", "Cryptography",      "[REAL] AES-256-GCM, RSA-2048-OAEP, CSPRNG. Drop-in replacement for PyCrypto."),
        ("Web Crypto API",    "Client crypto",     "[REAL] Native browser crypto — AES-GCM, RSA-OAEP, secure random. No JS library needed."),
        ("Docker",            "Containerisation",  "Multi-stage build produces a minimal runtime image. Non-root user enforced."),
        ("Nginx",             "Static file server","Serves the frontend dashboard. Reverse proxy to backend in production."),
        ("pytest",            "Testing",           "Unit + integration tests. pytest-asyncio for async route testing."),
        ("Chart.js 4",        "Dashboard charts",  "CDN-loaded. Used only in the frontend HTML report — no build step needed."),
        ("python-docx",       "Documentation",     "Generates this Word document programmatically."),
    ]
    add_table(doc, ["Technology", "Role", "Why Chosen"], tech)

    heading2(doc, "3.1 Why pycryptodome?")
    body(doc,
        "pycryptodome is the most widely used Python cryptography library for symmetric and "
        "asymmetric primitives. It implements AES in hardware-accelerated GCM mode and RSA "
        "with OAEP/SHA-256 padding — both NIST-recommended for 2024+. Unlike the 'cryptography' "
        "library (which wraps OpenSSL), pycryptodome is a pure-Python fallback implementation "
        "that works identically on all platforms without native bindings, making it ideal for "
        "a Docker-containerised student project."
    )

    heading2(doc, "3.2 Why AES-256-GCM?")
    body(doc,
        "AES-256-GCM (Galois/Counter Mode) provides both confidentiality and integrity in a "
        "single pass. The 128-bit authentication tag (GCM tag) guarantees that any bit-flip "
        "in the ciphertext is detected and rejected before decryption — preventing padding "
        "oracle, chosen-ciphertext, and bit-flipping attacks."
    )

    heading2(doc, "3.3 Why RSA-2048-OAEP?")
    body(doc,
        "RSA-OAEP (Optimal Asymmetric Encryption Padding with SHA-256) is the current standard "
        "for RSA encryption. It prevents the classic RSA textbook attacks (small-e attack, "
        "broadcast attack, chosen-plaintext attack) through probabilistic padding. The session "
        "key exchange follows the same pattern as TLS 1.2 key exchange — well understood and "
        "thoroughly analysed by the cryptographic community."
    )

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 4 — Folder Structure
# ══════════════════════════════════════════════════════════════════════════════

def ch4_folder_structure(doc: Document):
    heading1(doc, "Chapter 4: Folder Structure")

    tree = """
tee-project/
├── backend/                          # FastAPI application
│   ├── main.py                       # App entry point, lifespan, CORS
│   ├── requirements.txt              # Python dependencies
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── inference.py              # POST /infer  (main endpoint)
│   │   ├── attestation.py            # GET /attest, GET /public-key
│   │   └── metrics.py                # GET /metrics
│   ├── core/
│   │   ├── __init__.py
│   │   ├── encryption.py             # AES-256-GCM + RSA-2048  [REAL]
│   │   ├── enclave.py                # Simulated TEE enclave    [SIMULATED]
│   │   ├── llm.py                    # DummyLLM + OpenAI LLM
│   │   └── attestation.py            # Quote generation/verify  [SIMULATED]
│   └── utils/
│       ├── __init__.py
│       ├── memory_guard.py           # Secure memory wipe       [REAL]
│       ├── privacy_analyzer.py       # PII detection + score    [REAL]
│       ├── nonce_tracker.py          # Replay attack prevention [REAL]
│       └── rate_limiter.py           # Per-IP rate limiting     [REAL]
│
├── frontend/
│   ├── index.html                    # Single-page dashboard
│   ├── css/styles.css                # Dark-themed styles
│   └── js/
│       ├── crypto.js                 # Web Crypto API wrappers  [REAL]
│       ├── api.js                    # /infer, /attest API calls
│       └── dashboard.js              # UI, charts, metrics poll
│
├── docker/
│   ├── Dockerfile                    # Multi-stage production build
│   ├── docker-compose.yml            # backend + nginx services
│   └── .dockerignore
│
├── tests/
│   ├── test_encryption.py
│   ├── test_inference.py
│   ├── test_attestation.py
│   └── test_memory_guard.py
│
├── scripts/
│   ├── setup.sh                      # One-time environment setup
│   ├── run_dev.sh                    # Start uvicorn dev server
│   └── demo_client.py                # End-to-end CLI demo
│
├── eval/
│   └── report_generator.py           # HTML performance report
│
├── docs/
│   ├── requirements.txt              # python-docx
│   └── generate_word_doc.py          # This script
│
└── README.md
"""
    code_block(doc, tree.strip())

    heading2(doc, "4.1 Design Decisions")
    decisions = [
        ("backend/core/",  "Core security primitives (crypto, enclave, attestation) are isolated here. No business logic bleeds in."),
        ("backend/utils/", "Cross-cutting concerns (memory, privacy, rate, nonce) that can be unit-tested independently."),
        ("backend/routers/","FastAPI routers handle HTTP concern only — they delegate all logic to core/ and utils/."),
        ("frontend/js/",    "Three files, each with a single responsibility: crypto, API communication, and UI."),
        ("docker/",         "Docker config is separate from application code, making it easy to swap out."),
    ]
    add_table(doc, ["Directory", "Rationale"], decisions)

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 5 — Backend Implementation
# ══════════════════════════════════════════════════════════════════════════════

def ch5_backend(doc: Document):
    heading1(doc, "Chapter 5: Backend Implementation")

    heading2(doc, "5.1 Application Entry Point — main.py")
    body(doc,
        "main.py uses FastAPI's lifespan context manager to initialise all in-memory state "
        "at startup and wipe it at shutdown. No file system writes occur during operation."
    )
    code_block(doc, read_source("backend/main.py"))

    heading2(doc, "5.2 Inference Router — routers/inference.py")
    body(doc,
        "The /infer endpoint is the heart of the system. It orchestrates the full "
        "decrypt → analyse → infer → re-encrypt → wipe pipeline."
    )
    code_block(doc, read_source("backend/routers/inference.py"))

    heading2(doc, "5.3 Attestation Router — routers/attestation.py")
    body(doc,
        "Provides GET /attest (full report), GET /public-key (RSA PEM), and POST /verify-quote."
    )
    code_block(doc, read_source("backend/routers/attestation.py"))

    heading2(doc, "5.4 Metrics Router — routers/metrics.py")
    code_block(doc, read_source("backend/routers/metrics.py"))

    heading2(doc, "5.5 Encryption Core — core/encryption.py")
    body(doc,
        "All cryptographic primitives. This is the only file that imports pycryptodome. "
        "Every function is pure (no side effects, no logging)."
    )
    code_block(doc, read_source("backend/core/encryption.py"))

    heading2(doc, "5.6 Enclave Simulation — core/enclave.py")
    body(doc,
        "Simulates Intel SGX isolation using a thread-locked in-memory dict. "
        "In production, replace this with a Gramine + SGX manifest."
    )
    code_block(doc, read_source("backend/core/enclave.py"))

    heading2(doc, "5.7 LLM Backend — core/llm.py")
    body(doc,
        "Factory pattern: DummyLLM is always available for testing; OpenAILLM activates "
        "when OPENAI_API_KEY is set. All inference runs inside the enclave context."
    )
    code_block(doc, read_source("backend/core/llm.py"))

    heading2(doc, "5.8 Attestation Core — core/attestation.py")
    code_block(doc, read_source("backend/core/attestation.py"))

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 6 — Encryption Deep Dive
# ══════════════════════════════════════════════════════════════════════════════

def ch6_encryption(doc: Document):
    heading1(doc, "Chapter 6: Encryption Deep Dive")

    heading2(doc, "6.1 Key Exchange Protocol")
    body(doc,
        "The system uses a hybrid encryption scheme — the same fundamental approach as TLS:"
    )
    steps = [
        ("1", "Server startup",      "Server generates RSA-2048 key pair. Private key stays in enclave memory."),
        ("2", "Public key delivery", "Client fetches the RSA public key via GET /public-key (over HTTPS)."),
        ("3", "Session key gen",     "Client generates a fresh AES-256 key for each request (ephemeral)."),
        ("4", "Prompt encryption",   "Prompt → AES-256-GCM(session_key) → {ciphertext, IV, tag}."),
        ("5", "Key wrapping",        "session_key → RSA-OAEP(server_public_key) → encrypted_session_key."),
        ("6", "Server decryption",   "Server: RSA-OAEP decrypt → session_key. AES-GCM decrypt → plaintext prompt."),
        ("7", "Response encryption", "Server: AES-GCM encrypt(response, session_key) → {ciphertext, new IV, tag}."),
        ("8", "Key discard",         "Session key wiped from server memory. Client discards it after decryption."),
    ]
    add_table(doc, ["Step", "Actor", "Operation"], steps)

    heading2(doc, "6.2 AES-256-GCM Explained")
    body(doc,
        "GCM (Galois/Counter Mode) is an authenticated encryption with associated data (AEAD) "
        "mode. It combines:"
    )
    bullet(doc, "CTR mode encryption — generates a keystream by encrypting successive counter values, then XORs with plaintext.")
    bullet(doc, "GHASH authentication — a polynomial hash over the ciphertext produces a 128-bit authentication tag.")
    body(doc,
        "The tag allows the receiver to detect any modification to the ciphertext before "
        "decryption. In pycryptodome, if the tag is wrong, AES.new(…).decrypt_and_verify() "
        "raises ValueError — the decryption fails loudly and safely."
    )

    heading2(doc, "6.3 IV/Nonce Management")
    body(doc,
        "Each AES-GCM encryption uses a fresh 96-bit (12-byte) IV generated by "
        "Crypto.Random.get_random_bytes(12). A secure CSPRNG (Cryptographically Secure "
        "Pseudo-Random Number Generator) is used — not Python's standard random module. "
        "IV reuse with the same key would be catastrophic (it breaks GCM's integrity guarantee), "
        "but since we use a fresh ephemeral session key per request, IV collision probability "
        "is astronomically low even if we reused IVs."
    )

    heading2(doc, "6.4 RSA-OAEP Explained")
    body(doc,
        "OAEP (Optimal Asymmetric Encryption Padding) adds randomness to RSA encryption, "
        "preventing: (a) deterministic encryption attacks where an attacker can test if a "
        "ciphertext decrypts to a known value; (b) CCA2 (adaptive chosen-ciphertext) attacks. "
        "SHA-256 is used as the hash function for the OAEP mask generation function (MGF1)."
    )

    heading2(doc, "6.5 Why Not TLS Alone?")
    body(doc,
        "TLS encrypts the network channel but terminates at the server — the server sees the "
        "plaintext. Our hybrid encryption scheme adds an application-layer encryption layer: "
        "the server only ever holds the RSA private key (inside the enclave), and decrypts the "
        "session key inside the enclave. The plaintext prompt is only ever present inside the "
        "enclave's isolated memory."
    )

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 7 — TEE / Enclave Simulation
# ══════════════════════════════════════════════════════════════════════════════

def ch7_tee(doc: Document):
    heading1(doc, "Chapter 7: TEE and Enclave Simulation")

    heading2(doc, "7.1 What Is a Trusted Execution Environment?")
    body(doc,
        "A Trusted Execution Environment is a secure area within a CPU that guarantees code "
        "and data loaded inside it are protected with respect to confidentiality and integrity. "
        "Even the host OS, hypervisor, and BIOS cannot read or tamper with enclave memory "
        "because the CPU encrypts it in hardware."
    )
    impls = [
        ("Intel SGX",       "Software Guard Extensions. Enclave pages encrypted by MEE (Memory Encryption Engine). Quote signed by CPU attestation key."),
        ("AMD SEV",         "Secure Encrypted Virtualization. Full VM memory encrypted. Used by cloud providers (Azure, GCP Confidential VMs)."),
        ("ARM TrustZone",   "Two worlds (secure/normal) on the same core. Used in mobile devices (Android Keystore, Secure Enclave on iPhone)."),
        ("AWS Nitro Enclave","Isolated VM with no persistent storage, no interactive access, cryptographic attestation."),
    ]
    add_table(doc, ["Technology", "Description"], impls)

    heading2(doc, "7.2 Our Simulation Approach")
    body(doc,
        "Since real Intel SGX hardware is not available in most student lab environments, "
        "we simulate the enclave with a Python class (EnclaveContext) that:"
    )
    bullet(doc, "Uses a threading.Lock() to ensure single-threaded access to isolated memory (mimics SGX's serialised execution model).")
    bullet(doc, "Stores intermediate values in a private dict (_isolated_memory) that is cleared on context exit.")
    bullet(doc, "Computes mrenclave and mrsigner as SHA-256 hashes (in real SGX these are CPU-computed hashes of the enclave binary).")
    bullet(doc, "Emits simulated attestation quotes as signed JSON blobs.")
    body(doc,
        "This simulation correctly demonstrates the architecture and all the software "
        "components. The privacy guarantees it provides are real (end-to-end encryption, "
        "memory wiping, no logging). The guarantee it does NOT provide compared to real SGX "
        "is hardware-enforced memory isolation — a privileged process on the same machine "
        "could in theory inspect the Python process memory."
    )

    heading2(doc, "7.3 Upgrading to Real Intel SGX with Gramine")
    body(doc,
        "Gramine (formerly Graphene-SGX) is a library OS that allows running unmodified Linux "
        "applications inside Intel SGX enclaves with minimal changes. Here is the step-by-step "
        "upgrade path:"
    )
    gramine_steps = """
# Step 1: Install SGX SDK and PSW on an SGX-capable machine
sudo apt-get install -y libsgx-enclave-common libsgx-urts libsgx-dcap-ql

# Step 2: Install Gramine
sudo apt-get install -y gramine

# Step 3: Create a Gramine manifest for the FastAPI backend
# File: backend.manifest.template
loader.entrypoint = "file:{{ gramine.libos }}"
loader.log_level = "error"
loader.argv = ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
fs.mounts = [
  { path = "/lib",   uri = "file:{{ gramine.runtimedir() }}" },
  { path = "/app",   uri = "file:/path/to/backend" },
]
sgx.debug = false
sgx.edmm_enable = {{ 'true' if env.get('EDMM', '0') == '1' else 'false' }}

# Step 4: Sign and build the manifest
gramine-sgx-sign --manifest backend.manifest --output backend.manifest.sgx

# Step 5: Run inside SGX
gramine-sgx python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# Step 6: Remote attestation (DCAP)
# The /attest endpoint now returns a real DCAP quote.
# Replace generate_quote() in core/attestation.py with:
#   from graminelibos import get_self_ra_quote
#   quote = get_self_ra_quote(user_data)
"""
    code_block(doc, gramine_steps.strip())

    heading2(doc, "7.4 Alternative: AWS Nitro Enclaves")
    body(doc,
        "If SGX hardware is unavailable, AWS Nitro Enclaves are an excellent alternative. "
        "Deploy the FastAPI backend as a Nitro Enclave inside an EC2 instance. The enclave "
        "communicates over a vsock channel with the parent instance. Attestation documents "
        "are signed by AWS KMS and include PCR measurements of the enclave image."
    )

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 8 — Frontend
# ══════════════════════════════════════════════════════════════════════════════

def ch8_frontend(doc: Document):
    heading1(doc, "Chapter 8: Frontend Implementation")

    heading2(doc, "8.1 Dashboard Overview")
    body(doc,
        "The frontend is a single HTML file (no build step, no npm). It uses:"
    )
    bullet(doc, "CSS Grid for responsive layout")
    bullet(doc, "Web Crypto API for client-side AES-256-GCM + RSA-OAEP (native browser, no library)")
    bullet(doc, "Chart.js (CDN) for the live metrics charts")
    bullet(doc, "Vanilla JS fetch() for API calls")

    heading2(doc, "8.2 Confidential Mode Toggle")
    body(doc,
        "When Confidential Mode is ON: all cryptographic operations are active. "
        "The prompt is encrypted before leaving the browser. "
        "When toggled OFF: a prominent warning banner appears informing the user that their "
        "prompt will be sent unencrypted (this mode exists for demo/comparison purposes only). "
        "In production, Confidential Mode OFF should be removed."
    )

    heading2(doc, "8.3 Client-Side Crypto — js/crypto.js")
    body(doc, "Uses Web Crypto API exclusively. No third-party crypto library.")
    code_block(doc, read_source("frontend/js/crypto.js"))

    heading2(doc, "8.4 API Communication — js/api.js")
    code_block(doc, read_source("frontend/js/api.js"))

    heading2(doc, "8.5 Dashboard Logic — js/dashboard.js")
    code_block(doc, read_source("frontend/js/dashboard.js"))

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 9 — Docker Deployment
# ══════════════════════════════════════════════════════════════════════════════

def ch9_docker(doc: Document):
    heading1(doc, "Chapter 9: Docker Deployment")

    heading2(doc, "9.1 Dockerfile")
    body(doc,
        "Multi-stage build: stage 1 installs dependencies, stage 2 is the minimal runtime "
        "image. Runs as a non-root user (teeuser, UID 1000)."
    )
    code_block(doc, read_source("docker/Dockerfile"))

    heading2(doc, "9.2 docker-compose.yml")
    code_block(doc, read_source("docker/docker-compose.yml"))

    heading2(doc, "9.3 Step-by-Step: Build and Run with Docker")
    steps_docker = """
# 0. Prerequisites
# Install Docker Desktop (Mac/Windows) or docker.io (Linux):
#   sudo apt-get install -y docker.io docker-compose-plugin

# 1. Clone / navigate to the project
cd tee-project

# 2. Build the images
docker compose -f docker/docker-compose.yml build

# 3. Start all services (backend + nginx)
docker compose -f docker/docker-compose.yml up -d

# 4. Verify backend is healthy
curl http://localhost:8000/health
# Expected: {"status":"healthy","uptime_seconds":...,"enclave_active":true}

# 5. Open the dashboard
open http://localhost:80            # nginx serves the frontend

# 6. View backend logs (should be minimal — no request logging)
docker compose -f docker/docker-compose.yml logs backend

# 7. Stop all services
docker compose -f docker/docker-compose.yml down
"""
    code_block(doc, steps_docker.strip())

    heading2(doc, "9.4 Environment Variables")
    env_vars = [
        ("OPENAI_API_KEY",     "",       "OpenAI API key. Leave empty to use DummyLLM."),
        ("PORT",               "8000",   "Port uvicorn listens on inside the container."),
        ("HOST",               "0.0.0.0","Bind address."),
        ("ENCLAVE_SIMULATION", "true",   "Set to false when using real SGX hardware + Gramine."),
        ("NO_LOGGING",         "true",   "Enforces no-logging policy (informational env var)."),
    ]
    add_table(doc, ["Variable", "Default", "Description"], env_vars)

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 10 — Testing
# ══════════════════════════════════════════════════════════════════════════════

def ch10_testing(doc: Document):
    heading1(doc, "Chapter 10: Testing")

    heading2(doc, "10.1 How to Run Tests")
    test_cmd = """
# Activate virtual environment
source .venv/bin/activate

# Install test dependencies (already in requirements.txt)
pip install pytest pytest-asyncio httpx

# Run all tests from project root
cd backend && pytest ../tests/ -v

# Run a single test file
pytest ../tests/test_encryption.py -v

# Run with coverage
pip install pytest-cov
pytest ../tests/ --cov=. --cov-report=term-missing -v
"""
    code_block(doc, test_cmd.strip())

    heading2(doc, "10.2 Test: Encryption (test_encryption.py)")
    code_block(doc, read_source("tests/test_encryption.py"))

    heading2(doc, "10.3 Test: Inference (test_inference.py)")
    code_block(doc, read_source("tests/test_inference.py"))

    heading2(doc, "10.4 Test: Attestation (test_attestation.py)")
    code_block(doc, read_source("tests/test_attestation.py"))

    heading2(doc, "10.5 Test: Memory Guard (test_memory_guard.py)")
    code_block(doc, read_source("tests/test_memory_guard.py"))

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 11 — Performance Evaluation
# ══════════════════════════════════════════════════════════════════════════════

def ch11_performance(doc: Document):
    heading1(doc, "Chapter 11: Performance Evaluation")

    heading2(doc, "11.1 Latency Components")
    body(doc,
        "Total end-to-end latency is the sum of four components:"
    )
    latency_comps = [
        ("Client AES-GCM encrypt",   "0.1–0.3 ms",  "Negligible. Browser AES hardware acceleration."),
        ("Client RSA-OAEP wrap",     "1–5 ms",       "Dominant client cost. 2048-bit modular exponentiation."),
        ("Network RTT",              "1–100+ ms",     "Depends entirely on network. Localhost: ~0.5 ms."),
        ("Server RSA-OAEP unwrap",   "2–8 ms",        "Server-side private-key operation (modular exponentiation)."),
        ("Server AES-GCM decrypt",   "0.05–0.2 ms",  "Negligible."),
        ("LLM inference (dummy)",    "0.01–0.1 ms",  "Dummy: dict lookup. Real GPT-3.5: 500–3000 ms."),
        ("LLM inference (GPT-3.5)",  "500–3000 ms",  "[REAL] Network latency to OpenAI API."),
        ("Server AES-GCM encrypt",   "0.05–0.2 ms",  "Negligible."),
        ("Client AES-GCM decrypt",   "0.1–0.3 ms",   "Negligible."),
    ]
    add_table(doc, ["Component", "Typical Time", "Notes"], latency_comps)

    heading2(doc, "11.2 Encryption Overhead Analysis")
    body(doc,
        "The encryption overhead (AES + RSA combined, client + server) is typically "
        "3–15 ms — less than 1% of the total latency when using a real LLM model. "
        "This overhead is the cost of the security guarantee and is considered "
        "acceptable for any practical deployment."
    )

    heading2(doc, "11.3 Generating the HTML Performance Report")
    body(doc,
        "The eval/report_generator.py script benchmarks the live server and produces a "
        "self-contained HTML report with interactive Chart.js charts:"
    )
    bench_cmd = """
# Start the backend first (in another terminal)
bash scripts/run_dev.sh

# Run 50 benchmark requests and generate the report
python eval/report_generator.py --requests 50 --out eval/report.html

# Open report in browser
open eval/report.html
"""
    code_block(doc, bench_cmd.strip())

    heading2(doc, "11.4 Performance Report Source")
    code_block(doc, read_source("eval/report_generator.py"))

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 12 — Security Evaluation
# ══════════════════════════════════════════════════════════════════════════════

def ch12_security(doc: Document):
    heading1(doc, "Chapter 12: Security Evaluation")

    heading2(doc, "12.1 Threat Model")
    threats = [
        ("Network eavesdropper", "Observes encrypted traffic on the wire.",
         "AES-256-GCM + TLS. No plaintext ever on the wire."),
        ("Malicious cloud provider", "Root access to the server host OS.",
         "Simulated: software isolation. Real SGX: hardware memory encryption."),
        ("Replay attacker", "Captures and replays a valid /infer request.",
         "Nonce tracker rejects duplicate UUIDs within 5-minute TTL."),
        ("Man-in-the-middle", "Substitutes the RSA public key.",
         "Attestation: client verifies mrenclave hash before trusting the key."),
        ("Prompt injection via ciphertext tampering", "Flips bits in ciphertext.",
         "AES-GCM authentication tag. Any tampering causes ValueError on decrypt."),
        ("DoS / rate abuse", "Floods the inference endpoint.",
         "Rate limiter: 60 req/min/IP. HTTP 429 on excess."),
        ("Log harvesting", "Extracts prompts from server logs.",
         "No logging middleware. No log files written."),
        ("Memory dump", "Reads server process memory after a request.",
         "MemoryGuard: session key and prompt overwritten with zeros immediately."),
    ]
    add_table(doc,
              ["Threat Actor", "Attack Vector", "Our Defence"],
              [(t[0], t[1], t[2]) for t in threats])

    heading2(doc, "12.2 Attack Simulations")
    body(doc,
        "The eval/report_generator.py script runs these three simulations automatically "
        "against the live server:"
    )

    heading3(doc, "12.2.1 Replay Attack")
    body(doc,
        "Send the same /infer request payload (identical nonce) twice. "
        "Expected: first request succeeds (HTTP 200), second is rejected (HTTP 400: "
        "'Invalid or replayed nonce'). The NonceTracker stores seen nonces in an in-memory "
        "set with a 5-minute TTL."
    )

    heading3(doc, "12.2.2 Ciphertext Tampering")
    body(doc,
        "XOR the first byte of the encrypted_prompt ciphertext with 0xFF before sending. "
        "Expected: server returns HTTP 500 because AES.decrypt_and_verify() raises "
        "ValueError('MAC check failed'). This confirms the authentication tag is working."
    )

    heading3(doc, "12.2.3 Plaintext Interception")
    body(doc,
        "Inspect the raw /infer POST body for a known PII string "
        "('My SSN is 123-45-6789'). Expected: the PII string is NOT present in the "
        "JSON payload — only base64-encoded ciphertext is transmitted."
    )

    heading2(doc, "12.3 Known Limitations (Simulation vs Hardware)")
    limits = [
        ("Process memory inspection", "A privileged process could ptrace the Python runtime and read memory. Real SGX prevents this."),
        ("Python GC", "Python's garbage collector may retain copies of strings. We use bytearray + ctypes to mitigate this, but it's not a 100% guarantee."),
        ("Side-channel attacks", "Real SGX protects against memory access patterns leakage via hardware features. Our simulation does not."),
        ("Key persistence", "RSA private key lives in the Python process. In real SGX, it would be sealed to the enclave identity."),
    ]
    add_table(doc, ["Limitation", "Impact and Mitigation"], limits)

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 13 — Privacy Score
# ══════════════════════════════════════════════════════════════════════════════

def ch13_privacy_score(doc: Document):
    heading1(doc, "Chapter 13: Privacy Score Feature")

    heading2(doc, "13.1 What Is the Privacy Score?")
    body(doc,
        "Every inference request is analysed for Personally Identifiable Information (PII) "
        "before it is passed to the LLM. The analysis produces a score from 0 (extremely "
        "high PII risk) to 100 (no PII detected). This score is returned to the client "
        "along with the encrypted response."
    )

    heading2(doc, "13.2 PII Detection Patterns")
    patterns = [
        ("email",         r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",    "20"),
        ("phone_us",      r"\b(\+1)?(\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{4}\b",         "15"),
        ("ssn",           r"\b\d{3}-\d{2}-\d{4}\b",                                     "40"),
        ("credit_card",   r"\b(?:\d[ \-]?){13,16}\b",                                    "35"),
        ("ipv4",          r"\b(?:\d{1,3}\.){3}\d{1,3}\b",                                "10"),
        ("date_of_birth", r"\b(dob|date of birth|born on)[:\s]+\d{1,2}[/\-]\d{1,2}...", "15"),
        ("passport",      r"\b[A-Z]{1,2}\d{6,9}\b",                                      "30"),
        ("name_pattern",  r"\b(my name is|i am|i'm)\s+[A-Z][a-z]+...\b",                "10"),
    ]
    add_table(doc, ["PII Type", "Regex Pattern (simplified)", "Penalty per match"], patterns)

    heading2(doc, "13.3 Scoring Formula")
    body(doc, "score = max(0, min(100,  100 − Σ(weight_i × count_i)))")
    body(doc,
        "Example: A text containing 1 SSN (penalty 40) and 1 email (penalty 20) "
        "receives score = 100 − 60 = 40, risk level HIGH."
    )
    body(doc, "Risk level mapping:")
    risk = [
        ("80–100", "LOW",      "Clean text or only minor PII."),
        ("50–79",  "MEDIUM",   "Some PII present (name, IP, phone)."),
        ("20–49",  "HIGH",     "Significant PII (SSN, credit card, multiple items)."),
        ("0–19",   "CRITICAL", "Multiple severe PII types."),
    ]
    add_table(doc, ["Score Range", "Risk Level", "Meaning"], risk)

    heading2(doc, "13.4 Privacy Score Module Source")
    code_block(doc, read_source("backend/utils/privacy_analyzer.py"))

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 14 — Confidential Mode
# ══════════════════════════════════════════════════════════════════════════════

def ch14_confidential_mode(doc: Document):
    heading1(doc, "Chapter 14: Confidential Mode")

    heading2(doc, "14.1 Feature Description")
    body(doc,
        "Confidential Mode is a UI toggle in the dashboard that controls whether "
        "the full encryption pipeline is active."
    )
    modes = [
        ("ON  (default)", "All cryptographic operations active. Prompt encrypted before leaving the browser. Green shield icon shown."),
        ("OFF (demo)",    "Prompt sent as plaintext. Large red warning banner displayed. For demonstration and comparison only."),
    ]
    add_table(doc, ["Mode", "Behaviour"], modes)

    heading2(doc, "14.2 Implementation Notes")
    body(doc,
        "When Confidential Mode is OFF, the frontend sends the prompt directly in the "
        "request body as plaintext_prompt instead of going through the encryption pipeline. "
        "The backend /infer endpoint checks for the encrypted_prompt field — if it receives "
        "a plaintext_prompt instead it still processes the request but bypasses decryption "
        "(this path is clearly marked for demonstration)."
    )
    body(doc,
        "In a production deployment, the OFF mode should be removed entirely. It exists "
        "in this project to let an instructor demonstrate the difference between encrypted "
        "and unencrypted operation side-by-side."
    )

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 15 — Future Improvements
# ══════════════════════════════════════════════════════════════════════════════

def ch15_future(doc: Document):
    heading1(doc, "Chapter 15: Future Improvements")

    improvements = [
        ("Real Intel SGX + Gramine",
         "Replace the simulated EnclaveContext with a Gramine-SGX manifest. "
         "Hardware memory encryption guarantees confidentiality even against root-level attackers."),
        ("DCAP Remote Attestation",
         "Integrate Intel's DCAP (Data Center Attestation Primitives) library so clients can "
         "cryptographically verify the enclave's mrenclave value against Intel's attestation service."),
        ("Homomorphic Encryption (HE)",
         "Future research direction: perform LLM inference on encrypted data without decrypting. "
         "Libraries: Microsoft SEAL, OpenFHE. Currently impractical for transformer models but "
         "active research area."),
        ("Federated Learning Integration",
         "Train the LLM without centralising data by combining TEE inference with federated "
         "learning — each participant trains locally and only shares encrypted gradients."),
        ("Persistent Enclave Key Sealing",
         "Use SGX key sealing to persist the RSA private key encrypted to the enclave identity, "
         "so it survives server restarts without re-distribution."),
        ("mTLS Client Authentication",
         "Add mutual TLS so the server can verify the client certificate, preventing anonymous "
         "access and adding an additional layer of authentication."),
        ("Rate Limit Persistence",
         "Move the rate limiter and nonce tracker to Redis so they survive process restarts "
         "and work correctly across multiple server instances (horizontal scaling)."),
        ("Differential Privacy in LLM Outputs",
         "Add calibrated Laplace/Gaussian noise to model logits to prevent membership inference "
         "attacks where an adversary deduces training data from model outputs."),
        ("WASM Crypto on Client",
         "For non-browser clients (Python, mobile), compile pycryptodome or libsodium to WASM "
         "for consistent cross-platform crypto performance."),
    ]

    for title, desc in improvements:
        heading2(doc, title)
        body(doc, desc)

    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX A — README
# ══════════════════════════════════════════════════════════════════════════════

def appendix_a_readme(doc: Document):
    heading1(doc, "Appendix A: README")
    readme = read_source("README.md")
    # Render README as code block to preserve formatting
    code_block(doc, readme)
    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX B — Source Code Listing
# ══════════════════════════════════════════════════════════════════════════════

def appendix_b_source(doc: Document):
    heading1(doc, "Appendix B: Full Source Code Listing")

    files = [
        ("backend/requirements.txt",          "Python dependencies"),
        ("backend/utils/nonce_tracker.py",     "Replay attack prevention"),
        ("backend/utils/rate_limiter.py",      "Rate limiter"),
        ("docker/.dockerignore",               "Docker build ignore rules"),
        ("scripts/setup.sh",                   "Environment setup script"),
        ("scripts/run_dev.sh",                 "Development server launcher"),
        ("scripts/demo_client.py",             "End-to-end demo client"),
        ("frontend/css/styles.css",            "Dashboard stylesheet"),
        ("frontend/index.html",                "Dashboard HTML"),
    ]

    for rel_path, description in files:
        heading2(doc, f"{rel_path}  —  {description}")
        code_block(doc, read_source(rel_path))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"[docgen] Building Word document…")
    doc = new_doc()
    add_footer_page_numbers(doc)

    build_title_page(doc)
    build_toc(doc)

    ch1_introduction(doc)
    ch2_architecture(doc)
    ch3_tech_stack(doc)
    ch4_folder_structure(doc)
    ch5_backend(doc)
    ch6_encryption(doc)
    ch7_tee(doc)
    ch8_frontend(doc)
    ch9_docker(doc)
    ch10_testing(doc)
    ch11_performance(doc)
    ch12_security(doc)
    ch13_privacy_score(doc)
    ch14_confidential_mode(doc)
    ch15_future(doc)
    appendix_a_readme(doc)
    appendix_b_source(doc)

    doc.save(str(OUT_FILE))
    print(f"[docgen] Done!  →  {OUT_FILE}")
    print(f"[docgen] Size:  {OUT_FILE.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
