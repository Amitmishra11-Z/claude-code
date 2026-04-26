/**
 * Client-side crypto using Web Crypto API.
 * # [REAL] — Uses browser's native SubtleCrypto (AES-256-GCM + RSA-OAEP)
 */

/**
 * Generate an AES-256-GCM session key.
 * @returns {Promise<CryptoKey>}
 */
async function generateSessionKey() {
  return await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,       // extractable (needed to export for RSA wrapping)
    ['encrypt', 'decrypt']
  );
}

/**
 * Encrypt plaintext with AES-256-GCM session key.
 * @param {CryptoKey} key
 * @param {string} plaintext
 * @returns {Promise<{ciphertext: string, iv: string, tag: string}>}  base64 strings
 */
async function encryptWithSessionKey(key, plaintext) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(plaintext);

  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv, tagLength: 128 },
    key,
    encoded
  );

  // AES-GCM output = ciphertext || tag (last 16 bytes)
  const encryptedArray = new Uint8Array(encrypted);
  const tagOffset = encryptedArray.length - 16;
  const ciphertext = encryptedArray.slice(0, tagOffset);
  const tag = encryptedArray.slice(tagOffset);

  return {
    ciphertext: arrayBufferToBase64(ciphertext),
    iv: arrayBufferToBase64(iv),
    tag: arrayBufferToBase64(tag),
  };
}

/**
 * Decrypt AES-256-GCM ciphertext.
 * @param {CryptoKey} key
 * @param {string} ciphertextB64
 * @param {string} ivB64
 * @param {string} tagB64
 * @returns {Promise<string>}
 */
async function decryptWithSessionKey(key, ciphertextB64, ivB64, tagB64) {
  const iv = base64ToArrayBuffer(ivB64);
  const ciphertext = base64ToArrayBuffer(ciphertextB64);
  const tag = base64ToArrayBuffer(tagB64);

  // Reassemble ciphertext+tag for SubtleCrypto
  const combined = new Uint8Array(ciphertext.byteLength + tag.byteLength);
  combined.set(new Uint8Array(ciphertext), 0);
  combined.set(new Uint8Array(tag), ciphertext.byteLength);

  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: new Uint8Array(iv), tagLength: 128 },
    key,
    combined
  );
  return new TextDecoder().decode(decrypted);
}

/**
 * Encrypt the raw session key bytes with the server's RSA-2048 public key.
 * @param {string} publicKeyPem  — PEM string from /public-key endpoint
 * @param {CryptoKey} sessionKey — AES CryptoKey to wrap
 * @returns {Promise<string>}    — base64 encoded RSA-OAEP ciphertext
 */
async function encryptSessionKeyWithRSA(publicKeyPem, sessionKey) {
  const pemBody = publicKeyPem
    .replace(/-----BEGIN PUBLIC KEY-----/, '')
    .replace(/-----END PUBLIC KEY-----/, '')
    .replace(/\s+/g, '');
  const binaryDer = base64ToArrayBuffer(pemBody);

  const rsaKey = await crypto.subtle.importKey(
    'spki',
    binaryDer,
    { name: 'RSA-OAEP', hash: 'SHA-1' },
    false,
    ['wrapKey']
  );

  const wrapped = await crypto.subtle.wrapKey('raw', sessionKey, rsaKey, {
    name: 'RSA-OAEP',
  });
  return arrayBufferToBase64(wrapped);
}

/**
 * Generate a UUID v4 nonce for replay prevention.
 * @returns {string}
 */
function generateNonce() {
  if (crypto.randomUUID) return crypto.randomUUID();
  const buf = crypto.getRandomValues(new Uint8Array(16));
  buf[6] = (buf[6] & 0x0f) | 0x40;
  buf[8] = (buf[8] & 0x3f) | 0x80;
  const hex = Array.from(buf).map(b => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function arrayBufferToBase64(buffer) {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function base64ToArrayBuffer(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}
