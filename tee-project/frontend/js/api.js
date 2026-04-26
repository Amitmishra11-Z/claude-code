/**
 * API client — talks to the FastAPI backend.
 */

const API_BASE = 'http://localhost:8000';

/**
 * Fetch the server's RSA public key.
 * @returns {Promise<string>} PEM string
 */
async function fetchPublicKey() {
  const res = await fetch(`${API_BASE}/public-key`);
  if (!res.ok) throw new Error('Failed to fetch public key');
  const data = await res.json();
  return data.public_key_pem;
}

/**
 * Fetch the attestation report.
 * @returns {Promise<object>}
 */
async function fetchAttestation() {
  const res = await fetch(`${API_BASE}/attest`);
  if (!res.ok) throw new Error('Failed to fetch attestation');
  return await res.json();
}

/**
 * Fetch runtime metrics.
 * @returns {Promise<object>}
 */
async function fetchMetrics() {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return await res.json();
}

/**
 * Send an encrypted inference request.
 * @param {object} payload
 * @returns {Promise<object>}
 */
async function sendInferRequest(payload) {
  const res = await fetch(`${API_BASE}/infer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Inference failed');
  }
  return await res.json();
}

/**
 * Check backend health.
 * @returns {Promise<object>}
 */
async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Backend unreachable');
  return await res.json();
}
