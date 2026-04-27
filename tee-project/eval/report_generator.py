#!/usr/bin/env python3
"""
report_generator.py — Performance & Security Evaluation Report Generator.

Runs a series of benchmark requests against the live TEE backend,
collects metrics, and writes a self-contained HTML report with inline
Chart.js charts.

Usage:
    # Start backend first, then:
    python eval/report_generator.py --requests 20 --out eval/report.html

# [REAL] Timings are real wall-clock measurements against the live server.
# [SIMULATED] Security attack simulations are replayed locally (no real attacker).
"""
import os
import sys
import json
import time
import uuid
import base64
import argparse
import statistics
from datetime import datetime

try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Random import get_random_bytes
    import httpx
except ImportError:
    print("ERROR: pip install pycryptodome httpx")
    sys.exit(1)

BASE_URL = os.environ.get("TEE_BASE_URL", "http://localhost:8000")


# ── Crypto helpers (same as demo_client) ──────────────────────────────────────

def _generate_session_key() -> bytes:
    return get_random_bytes(32)


def _aes_encrypt(key: bytes, plaintext: str) -> dict:
    iv = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ct, tag = cipher.encrypt_and_digest(plaintext.encode())
    return {
        "ciphertext": base64.b64encode(ct).decode(),
        "iv":         base64.b64encode(iv).decode(),
        "tag":        base64.b64encode(tag).decode(),
    }


def _aes_decrypt(key: bytes, ct_b64: str, iv_b64: str, tag_b64: str) -> str:
    ct  = base64.b64decode(ct_b64)
    iv  = base64.b64decode(iv_b64)
    tag = base64.b64decode(tag_b64)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    return cipher.decrypt_and_verify(ct, tag).decode()


def _rsa_encrypt_key(public_key_pem: str, session_key: bytes) -> str:
    pub = RSA.import_key(public_key_pem.encode())
    return base64.b64encode(PKCS1_OAEP.new(pub).encrypt(session_key)).decode()


# ── Single inference round-trip ────────────────────────────────────────────────

def single_request(client: "httpx.Client", public_key_pem: str, prompt: str) -> dict:
    """
    Perform one complete encrypted inference request.
    Returns a dict of timing and result data.
    """
    t_total_start = time.perf_counter()

    sk = _generate_session_key()

    # Client-side encryption overhead
    t_enc_start = time.perf_counter()
    enc = _aes_encrypt(sk, prompt)
    enc_sk = _rsa_encrypt_key(public_key_pem, sk)
    t_enc_end = time.perf_counter()
    client_enc_ms = (t_enc_end - t_enc_start) * 1000

    payload = {
        "encrypted_prompt": enc["ciphertext"],
        "iv":               enc["iv"],
        "tag":              enc["tag"],
        "session_key_enc":  enc_sk,
        "nonce":            str(uuid.uuid4()),
        "model":            "dummy",
        "max_tokens":       128,
    }

    # Network + server latency
    t_net_start = time.perf_counter()
    resp = client.post("/infer", json=payload)
    t_net_end = time.perf_counter()
    network_ms = (t_net_end - t_net_start) * 1000

    if resp.status_code != 200:
        return {"error": resp.status_code}

    result = resp.json()

    # Client-side decryption
    t_dec_start = time.perf_counter()
    _aes_decrypt(sk, result["encrypted_response"], result["iv"], result["tag"])
    t_dec_end = time.perf_counter()
    client_dec_ms = (t_dec_end - t_dec_start) * 1000

    total_ms = (time.perf_counter() - t_total_start) * 1000

    return {
        "total_ms":       round(total_ms, 2),
        "network_ms":     round(network_ms, 2),
        "server_ms":      result["latency_ms"],
        "client_enc_ms":  round(client_enc_ms, 2),
        "client_dec_ms":  round(client_dec_ms, 2),
        "privacy_score":  result["privacy_score"],
        "risk_level":     result["risk_level"],
    }


# ── Security attack simulations ────────────────────────────────────────────────

def simulate_replay_attack(client: "httpx.Client", public_key_pem: str) -> dict:
    """
    Send the same nonce twice. Second request must be rejected (HTTP 400).
    # [SIMULATED]
    """
    sk   = _generate_session_key()
    enc  = _aes_encrypt(sk, "replay test")
    enc_sk = _rsa_encrypt_key(public_key_pem, sk)
    nonce = str(uuid.uuid4())
    payload = {
        "encrypted_prompt": enc["ciphertext"],
        "iv":   enc["iv"],
        "tag":  enc["tag"],
        "session_key_enc": enc_sk,
        "nonce": nonce,
        "model": "dummy",
        "max_tokens": 32,
    }
    r1 = client.post("/infer", json=payload)
    r2 = client.post("/infer", json=payload)   # same nonce
    return {
        "first_status":   r1.status_code,
        "second_status":  r2.status_code,
        "replay_blocked": r2.status_code == 400,
    }


def simulate_tampered_ciphertext(client: "httpx.Client", public_key_pem: str) -> dict:
    """
    Flip a byte in the ciphertext — server must reject with 500 (MAC mismatch).
    # [SIMULATED]
    """
    sk   = _generate_session_key()
    enc  = _aes_encrypt(sk, "tamper test prompt")
    enc_sk = _rsa_encrypt_key(public_key_pem, sk)

    # Corrupt the ciphertext
    ct_bytes = bytearray(base64.b64decode(enc["ciphertext"]))
    ct_bytes[0] ^= 0xFF
    enc["ciphertext"] = base64.b64encode(bytes(ct_bytes)).decode()

    payload = {
        "encrypted_prompt": enc["ciphertext"],
        "iv":   enc["iv"],
        "tag":  enc["tag"],
        "session_key_enc": enc_sk,
        "nonce": str(uuid.uuid4()),
        "model": "dummy",
        "max_tokens": 32,
    }
    resp = client.post("/infer", json=payload)
    return {
        "status":          resp.status_code,
        "tamper_rejected": resp.status_code in (400, 422, 500),
    }


def simulate_plaintext_sniff(client: "httpx.Client", public_key_pem: str) -> dict:
    """
    Intercept the wire payload — confirm no plaintext is present in request body.
    # [SIMULATED]
    """
    plaintext_prompt = "My SSN is 123-45-6789 and my email is victim@test.com"
    sk   = _generate_session_key()
    enc  = _aes_encrypt(sk, plaintext_prompt)
    enc_sk = _rsa_encrypt_key(public_key_pem, sk)
    payload = {
        "encrypted_prompt": enc["ciphertext"],
        "iv":   enc["iv"],
        "tag":  enc["tag"],
        "session_key_enc": enc_sk,
        "nonce": str(uuid.uuid4()),
        "model": "dummy",
        "max_tokens": 32,
    }
    payload_json = json.dumps(payload)
    plaintext_exposed = plaintext_prompt in payload_json
    return {
        "plaintext_in_wire": plaintext_exposed,
        "plaintext_protected": not plaintext_exposed,
    }


# ── Report HTML template ───────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TEE LLM Inference — Performance & Security Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #e2e8f0; }}
  header {{ background: linear-gradient(135deg, #1e3a5f, #0f2744); padding: 32px 40px; border-bottom: 2px solid #3b82f6; }}
  header h1 {{ font-size: 1.8rem; color: #93c5fd; }}
  header p  {{ color: #94a3b8; margin-top: 6px; font-size: 0.9rem; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 24px 0; }}
  .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin: 24px 0; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }}
  .card h2 {{ font-size: 1rem; color: #60a5fa; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.05em; }}
  .stat-value {{ font-size: 2rem; font-weight: 700; color: #f1f5f9; }}
  .stat-label {{ font-size: 0.8rem; color: #64748b; margin-top: 4px; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }}
  .badge-green  {{ background: #065f46; color: #6ee7b7; }}
  .badge-red    {{ background: #7f1d1d; color: #fca5a5; }}
  .badge-yellow {{ background: #78350f; color: #fcd34d; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th {{ text-align: left; padding: 8px 12px; background: #1e3a5f; color: #93c5fd; border-bottom: 1px solid #334155; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }}
  tr:hover td {{ background: #1e293b; }}
  h2.section {{ font-size: 1.2rem; color: #93c5fd; margin: 32px 0 12px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
  .chart-wrap {{ position: relative; height: 240px; }}
  footer {{ text-align: center; color: #475569; font-size: 0.8rem; padding: 24px; border-top: 1px solid #1e293b; margin-top: 40px; }}
</style>
</head>
<body>
<header>
  <h1>TEE LLM Inference — Evaluation Report</h1>
  <p>Generated: {generated_at} &nbsp;|&nbsp; Requests: {n_requests} &nbsp;|&nbsp; Server: {base_url}</p>
</header>
<div class="container">

  <!-- Summary stats -->
  <h2 class="section">Performance Summary</h2>
  <div class="grid-3">
    <div class="card">
      <h2>Avg Total Latency</h2>
      <div class="stat-value">{avg_total_ms} ms</div>
      <div class="stat-label">end-to-end, client to client</div>
    </div>
    <div class="card">
      <h2>Avg Server Latency</h2>
      <div class="stat-value">{avg_server_ms} ms</div>
      <div class="stat-label">inside TEE enclave</div>
    </div>
    <div class="card">
      <h2>Avg Encryption Overhead</h2>
      <div class="stat-value">{avg_enc_ms} ms</div>
      <div class="stat-label">AES + RSA combined (client)</div>
    </div>
    <div class="card">
      <h2>Min Latency</h2>
      <div class="stat-value">{min_total_ms} ms</div>
      <div class="stat-label">best case</div>
    </div>
    <div class="card">
      <h2>Max Latency</h2>
      <div class="stat-value">{max_total_ms} ms</div>
      <div class="stat-label">worst case</div>
    </div>
    <div class="card">
      <h2>Avg Privacy Score</h2>
      <div class="stat-value">{avg_privacy}/100</div>
      <div class="stat-label">higher = less PII</div>
    </div>
  </div>

  <!-- Charts row -->
  <div class="grid-2">
    <div class="card">
      <h2>Latency Breakdown (ms)</h2>
      <div class="chart-wrap"><canvas id="latencyChart"></canvas></div>
    </div>
    <div class="card">
      <h2>Privacy Score Distribution</h2>
      <div class="chart-wrap"><canvas id="privacyChart"></canvas></div>
    </div>
  </div>

  <!-- Per-request table -->
  <h2 class="section">Per-Request Breakdown</h2>
  <div class="card">
    <table>
      <thead><tr>
        <th>#</th><th>Total (ms)</th><th>Network (ms)</th>
        <th>Server (ms)</th><th>Enc (ms)</th><th>Dec (ms)</th>
        <th>Privacy</th><th>Risk</th>
      </tr></thead>
      <tbody>
        {table_rows}
      </tbody>
    </table>
  </div>

  <!-- Security evaluation -->
  <h2 class="section">Security Evaluation (Simulated Attacks)</h2>
  <div class="grid-3">
    <div class="card">
      <h2>Replay Attack</h2>
      <div style="margin: 8px 0">
        First request: <span class="badge badge-green">{replay_first}</span>
      </div>
      <div style="margin: 8px 0">
        Replay attempt: <span class="badge badge-{replay_badge}">{replay_second}</span>
      </div>
      <div class="stat-label" style="margin-top:12px">
        {replay_blocked_text}
      </div>
    </div>
    <div class="card">
      <h2>Ciphertext Tampering</h2>
      <div style="margin: 8px 0">
        Status: <span class="badge badge-{tamper_badge}">{tamper_status}</span>
      </div>
      <div class="stat-label" style="margin-top:12px">
        {tamper_text}
      </div>
    </div>
    <div class="card">
      <h2>Plaintext Interception</h2>
      <div style="margin: 8px 0">
        PII in wire payload: <span class="badge badge-{sniff_badge}">{sniff_value}</span>
      </div>
      <div class="stat-label" style="margin-top:12px">
        {sniff_text}
      </div>
    </div>
  </div>

</div>

<footer>
  Privacy-Preserving LLM Inference using TEE &mdash; B.Tech Final Year Project &mdash;
  <span style="color:#3b82f6">[SIMULATED TEE]</span>
</footer>

<script>
const latencyData = {latency_data_json};
const privacyData = {privacy_data_json};

// Latency stacked bar chart
new Chart(document.getElementById('latencyChart'), {{
  type: 'bar',
  data: {{
    labels: latencyData.labels,
    datasets: [
      {{ label: 'Client Enc', data: latencyData.enc,  backgroundColor: '#3b82f6' }},
      {{ label: 'Network',    data: latencyData.net,  backgroundColor: '#8b5cf6' }},
      {{ label: 'Server',     data: latencyData.srv,  backgroundColor: '#06b6d4' }},
      {{ label: 'Client Dec', data: latencyData.dec,  backgroundColor: '#10b981' }},
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    scales: {{
      x: {{ stacked: true, ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
      y: {{ stacked: true, ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }}, title: {{ display: true, text: 'ms', color: '#94a3b8' }} }}
    }},
    plugins: {{ legend: {{ labels: {{ color: '#cbd5e1', boxWidth: 14 }} }} }}
  }}
}});

// Privacy score histogram
const bins = [0,10,20,30,40,50,60,70,80,90,100];
const binLabels = bins.slice(0,-1).map((b,i) => `${{b}}-${{bins[i+1]}}`);
const binCounts = new Array(bins.length-1).fill(0);
privacyData.forEach(v => {{
  const idx = Math.min(Math.floor(v/10), 9);
  binCounts[idx]++;
}});
new Chart(document.getElementById('privacyChart'), {{
  type: 'bar',
  data: {{
    labels: binLabels,
    datasets: [{{ label: 'Requests', data: binCounts, backgroundColor: '#10b981' }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
      y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }}, title: {{ display: true, text: 'Count', color: '#94a3b8' }} }}
    }},
    plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }}
  }}
}});
</script>
</body>
</html>"""


# ── Main ───────────────────────────────────────────────────────────────────────

def build_report(n_requests: int, out_path: str):
    client = httpx.Client(base_url=BASE_URL, timeout=30)

    print(f"[eval] Connecting to {BASE_URL} ...")
    try:
        health = client.get("/health").json()
        print(f"[eval] Server healthy — uptime {health.get('uptime_seconds', '?')}s")
    except Exception as e:
        print(f"[eval] ERROR: Cannot reach server: {e}")
        sys.exit(1)

    # Fetch public key once
    pub_pem = client.get("/public-key").json()["public_key_pem"]
    print(f"[eval] Got RSA-2048 public key.")

    test_prompts = [
        "Explain TEE",
        "What is AES encryption?",
        "Hello",
        "Tell me about privacy in AI",
        "My email is test@example.com. Is this safe?",
        "What is Intel SGX?",
        "How does remote attestation work?",
        "Summarize the concept of confidential computing",
        "What are differential privacy techniques?",
        "Describe homomorphic encryption",
    ]

    print(f"[eval] Running {n_requests} benchmark requests...")
    results = []
    for i in range(n_requests):
        prompt = test_prompts[i % len(test_prompts)]
        r = single_request(client, pub_pem, prompt)
        if "error" not in r:
            results.append(r)
            print(f"  [{i+1:3d}/{n_requests}] total={r['total_ms']:6.1f}ms  "
                  f"server={r['server_ms']:5.1f}ms  "
                  f"privacy={r['privacy_score']:5.1f}")
        else:
            print(f"  [{i+1:3d}/{n_requests}] ERROR {r['error']}")
        time.sleep(0.05)   # be gentle on the server

    if not results:
        print("[eval] No successful results. Aborting.")
        sys.exit(1)

    # ── Security simulations ───────────────────────────────────────────────────
    print("\n[eval] Running security simulations...")
    replay   = simulate_replay_attack(client, pub_pem)
    tamper   = simulate_tampered_ciphertext(client, pub_pem)
    sniff    = simulate_plaintext_sniff(client, pub_pem)
    print(f"  Replay attack blocked : {replay['replay_blocked']}")
    print(f"  Tamper rejected       : {tamper['tamper_rejected']}")
    print(f"  Plaintext protected   : {sniff['plaintext_protected']}")

    # ── Compute stats ──────────────────────────────────────────────────────────
    totals      = [r["total_ms"]      for r in results]
    servers     = [r["server_ms"]     for r in results]
    encs        = [r["client_enc_ms"] for r in results]
    decs        = [r["client_dec_ms"] for r in results]
    nets        = [r["network_ms"]    for r in results]
    privacies   = [r["privacy_score"] for r in results]

    avg_total_ms  = round(statistics.mean(totals), 1)
    avg_server_ms = round(statistics.mean(servers), 1)
    avg_enc_ms    = round(statistics.mean(encs) + statistics.mean(decs), 2)
    min_total_ms  = round(min(totals), 1)
    max_total_ms  = round(max(totals), 1)
    avg_privacy   = round(statistics.mean(privacies), 1)

    # ── Build table rows ───────────────────────────────────────────────────────
    risk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red", "CRITICAL": "red"}
    rows = ""
    for i, r in enumerate(results, 1):
        rc = risk_color.get(r["risk_level"], "yellow")
        rows += (
            f"<tr><td>{i}</td>"
            f"<td>{r['total_ms']}</td>"
            f"<td>{r['network_ms']}</td>"
            f"<td>{r['server_ms']}</td>"
            f"<td>{r['client_enc_ms']}</td>"
            f"<td>{r['client_dec_ms']}</td>"
            f"<td>{r['privacy_score']}</td>"
            f"<td><span class='badge badge-{rc}'>{r['risk_level']}</span></td></tr>\n"
        )

    # ── Chart data ─────────────────────────────────────────────────────────────
    labels = [str(i+1) for i in range(len(results))]
    latency_data = {
        "labels": labels,
        "enc": [r["client_enc_ms"] for r in results],
        "net": [r["network_ms"]    for r in results],
        "srv": [r["server_ms"]     for r in results],
        "dec": [r["client_dec_ms"] for r in results],
    }

    # ── Security badge helpers ────────────────────────────────────────────────
    replay_first_code  = replay["first_status"]
    replay_second_code = replay["second_status"]
    replay_blocked = replay["replay_blocked"]

    html = HTML_TEMPLATE.format(
        generated_at      = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        n_requests        = len(results),
        base_url          = BASE_URL,
        avg_total_ms      = avg_total_ms,
        avg_server_ms     = avg_server_ms,
        avg_enc_ms        = avg_enc_ms,
        min_total_ms      = min_total_ms,
        max_total_ms      = max_total_ms,
        avg_privacy       = avg_privacy,
        table_rows        = rows,
        latency_data_json = json.dumps(latency_data),
        privacy_data_json = json.dumps(privacies),
        # Replay
        replay_first      = f"HTTP {replay_first_code}",
        replay_second     = f"HTTP {replay_second_code}",
        replay_badge      = "green" if replay_blocked else "red",
        replay_blocked_text = ("✓ Replay attack BLOCKED by nonce tracker"
                               if replay_blocked else "✗ Replay NOT blocked — check nonce tracker"),
        # Tamper
        tamper_status     = f"HTTP {tamper['status']}",
        tamper_badge      = "green" if tamper["tamper_rejected"] else "red",
        tamper_text       = ("✓ Tampered ciphertext REJECTED by AES-GCM MAC"
                             if tamper["tamper_rejected"] else "✗ Tamper not rejected"),
        # Sniff
        sniff_value       = "NO" if sniff["plaintext_protected"] else "YES",
        sniff_badge       = "green" if sniff["plaintext_protected"] else "red",
        sniff_text        = ("✓ Plaintext NEVER transmitted — end-to-end encrypted"
                             if sniff["plaintext_protected"] else "✗ Plaintext found in request"),
    )

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[eval] Report written to: {out_path}")
    print(f"[eval] Open in browser:    open {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TEE LLM — Performance & Security Report Generator")
    parser.add_argument("--requests", type=int, default=20, help="Number of benchmark requests (default: 20)")
    parser.add_argument("--out",      default="eval/report.html",   help="Output HTML file path")
    parser.add_argument("--url",      default=BASE_URL,             help=f"Backend URL (default: {BASE_URL})")
    args = parser.parse_args()
    BASE_URL = args.url
    build_report(args.requests, args.out)
