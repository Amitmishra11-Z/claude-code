/**
 * Dashboard controller — wires UI to crypto.js and api.js.
 */

// ── State ─────────────────────────────────────────────────────────────────────
const state = {
  publicKey: null,
  sessionKey: null,
  confidentialMode: true,
  metricsInterval: null,
};

// ── DOM references ────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await initializeApp();
  setupEventListeners();
  startMetricsPoller();
});

async function initializeApp() {
  updateStatus('connecting', 'Connecting to enclave...');
  try {
    const health = await checkHealth();
    updateStatus('connected', 'Enclave connected');

    const attest = await fetchAttestation();
    updateAttestationPanel(attest);

    state.publicKey = await fetchPublicKey();

    const metrics = await fetchMetrics();
    updateMetrics(metrics);
  } catch (e) {
    updateStatus('error', 'Backend unreachable — start the server first');
    console.warn('Init error:', e.message);
  }
}

function setupEventListeners() {
  // Confidential Mode toggle
  $('confidential-toggle').addEventListener('change', e => {
    state.confidentialMode = e.target.checked;
    $('warning-banner').classList.toggle('visible', !state.confidentialMode);
  });

  // Theme toggle
  $('theme-toggle').addEventListener('change', e => {
    document.documentElement.setAttribute('data-theme', e.target.checked ? 'light' : 'dark');
  });

  // Send button
  $('send-btn').addEventListener('click', handleSend);

  // Enter key in prompt (Ctrl+Enter)
  $('prompt-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSend();
  });
}

async function handleSend() {
  const prompt = $('prompt-input').value.trim();
  if (!prompt) return;
  if (!state.publicKey) {
    showError('Public key not loaded — check backend connection.');
    return;
  }

  setLoading(true);
  clearResponse();

  try {
    const t0 = performance.now();

    // 1. Generate session key
    state.sessionKey = await generateSessionKey();

    // 2. Encrypt prompt with AES-256-GCM
    const { ciphertext, iv, tag } = await encryptWithSessionKey(state.sessionKey, prompt);

    // 3. Wrap session key with server RSA public key
    const sessionKeyEnc = await encryptSessionKeyWithRSA(state.publicKey, state.sessionKey);

    // 4. Generate nonce
    const nonce = generateNonce();

    // Show encrypted payload preview
    showEncryptedPayload({ ciphertext, iv });

    // 5. Send to backend
    const response = await sendInferRequest({
      encrypted_prompt: ciphertext,
      iv,
      tag,
      session_key_enc: sessionKeyEnc,
      nonce,
      model: 'dummy',
      max_tokens: 512,
    });

    const t1 = performance.now();

    // 6. Decrypt response
    const plaintext = await decryptWithSessionKey(
      state.sessionKey,
      response.encrypted_response,
      response.iv,
      response.tag,
    );

    showResponse(plaintext, response, t1 - t0);
    updatePrivacyScore(response.privacy_score, response.risk_level);

    // Refresh metrics
    const metrics = await fetchMetrics();
    updateMetrics(metrics);

  } catch (e) {
    showError(e.message);
  } finally {
    setLoading(false);
  }
}

// ── UI helpers ────────────────────────────────────────────────────────────────

function updateStatus(type, msg) {
  const led = $('status-led');
  const label = $('status-label');
  led.className = 'led ' + (type === 'connected' ? 'led-green' : 'led-red');
  label.textContent = msg;
}

function updateAttestationPanel(report) {
  $('attest-mrenclave').textContent = report.mrenclave || '—';
  $('attest-mrsigner').textContent = report.mrsigner || '—';
  $('attest-trust').textContent = report.trust_level || '—';
  $('attest-uptime').textContent = report.enclave_uptime_s + 's';
  const badge = $('attest-badge');
  badge.textContent = report.trust_level === 'HARDWARE' ? 'VERIFIED' : 'SIMULATED';
  badge.className = 'badge ' + (report.trust_level === 'HARDWARE' ? 'badge-success' : 'badge-warning');
}

function updateMetrics(m) {
  setText('metric-total', m.total_requests);
  setText('metric-latency', (m.avg_latency_ms || 0).toFixed(1) + ' ms');
  setText('metric-enc-overhead', (m.encryption_overhead_ms || 0).toFixed(1) + ' ms');
  setText('metric-privacy', (m.privacy_score_avg || 100).toFixed(0));
  setText('metric-uptime', Math.round(m.enclave_uptime_s) + 's');
  setText('metric-nonces', m.nonce_cache_size);
}

function updatePrivacyScore(score, risk) {
  $('gauge-value').textContent = score.toFixed(0);
  const color = score >= 80 ? '#2ed573' : score >= 50 ? '#ffa502' : '#ff4757';
  $('gauge-value').style.color = color;
  $('gauge-risk').textContent = risk;
  $('gauge-risk').style.color = color;
  // Update SVG arc
  const pct = score / 100;
  const r = 70, cx = 80, cy = 80;
  const angle = pct * Math.PI;
  const x = cx - r * Math.cos(angle);
  const y = cy - r * Math.sin(angle);
  const largeArc = pct > 0.5 ? 1 : 0;
  $('gauge-arc').setAttribute('d', `M ${cx-r},${cy} A ${r},${r} 0 ${largeArc},1 ${x.toFixed(1)},${y.toFixed(1)}`);
  $('gauge-arc').setAttribute('stroke', color);
}

function showResponse(plaintext, response, clientLatency) {
  $('response-box').textContent = plaintext;
  $('response-meta').innerHTML = `
    <span class="badge badge-success">Decrypted &#10003;</span>
    <span style="color:var(--text-muted);font-size:0.8rem;margin-left:0.5rem">
      Server: ${response.latency_ms}ms | Client total: ${clientLatency.toFixed(0)}ms
    </span>
  `;
}

function showEncryptedPayload({ ciphertext, iv }) {
  $('encrypted-preview').textContent = `IV: ${iv}\nCiphertext: ${ciphertext.substring(0, 80)}...`;
}

function clearResponse() {
  $('response-box').textContent = '';
  $('response-meta').innerHTML = '';
  $('encrypted-preview').textContent = '';
}

function showError(msg) {
  $('response-box').textContent = 'Error: ' + msg;
  $('response-box').style.color = 'var(--danger)';
  setTimeout(() => { $('response-box').style.color = ''; }, 3000);
}

function setLoading(loading) {
  const btn = $('send-btn');
  btn.disabled = loading;
  btn.innerHTML = loading
    ? '<span class="spinner"></span> Processing...'
    : '&#128274; Encrypt &amp; Send';
}

function setText(id, val) {
  const el = $(id);
  if (el) el.textContent = val;
}

function startMetricsPoller() {
  state.metricsInterval = setInterval(async () => {
    try {
      const m = await fetchMetrics();
      updateMetrics(m);
    } catch (_) {}
  }, 5000);
}
