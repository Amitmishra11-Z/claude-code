"""
AES-256-GCM + RSA-2048 encryption utilities.
# [REAL] All crypto uses pycryptodome — real cryptographic primitives
"""
import os
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes


def generate_rsa_keypair(bits: int = 2048):
    """Generate RSA-2048 key pair. Returns (private_key, public_key)."""
    key = RSA.generate(bits)
    private_key = key
    public_key = key.publickey()
    return private_key, public_key


def export_public_key_pem(public_key) -> str:
    """Export RSA public key as PEM string."""
    return public_key.export_key("PEM").decode("utf-8")


def export_private_key_pem(private_key) -> str:
    """Export RSA private key as PEM string."""
    return private_key.export_key("PEM").decode("utf-8")


def import_public_key_pem(pem: str):
    """Import RSA public key from PEM string."""
    return RSA.import_key(pem.encode("utf-8"))


def import_private_key_pem(pem: str):
    """Import RSA private key from PEM string."""
    return RSA.import_key(pem.encode("utf-8"))


def encrypt_with_rsa(public_key, data: bytes) -> bytes:
    """Encrypt data with RSA public key using OAEP padding. # [REAL]"""
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data)


def decrypt_with_rsa(private_key, data: bytes) -> bytes:
    """Decrypt data with RSA private key using OAEP padding. # [REAL]"""
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(data)


def generate_session_key() -> bytes:
    """Generate a 256-bit (32-byte) AES session key. # [REAL]"""
    return get_random_bytes(32)


def aes_encrypt(key: bytes, plaintext: bytes) -> dict:
    """
    AES-256-GCM encrypt. # [REAL]
    Returns dict with keys: ciphertext (bytes), iv (bytes), tag (bytes)
    """
    iv = get_random_bytes(12)  # 96-bit nonce recommended for GCM
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return {
        "ciphertext": ciphertext,
        "iv": iv,
        "tag": tag,
    }


def aes_decrypt(key: bytes, ciphertext: bytes, iv: bytes, tag: bytes) -> bytes:
    """AES-256-GCM decrypt with authentication. # [REAL]"""
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext


def aes_encrypt_b64(key: bytes, plaintext: str) -> dict:
    """Encrypt plaintext string, return base64-encoded components."""
    result = aes_encrypt(key, plaintext.encode("utf-8"))
    return {
        "ciphertext": base64.b64encode(result["ciphertext"]).decode(),
        "iv": base64.b64encode(result["iv"]).decode(),
        "tag": base64.b64encode(result["tag"]).decode(),
    }


def aes_decrypt_b64(key: bytes, ciphertext_b64: str, iv_b64: str, tag_b64: str) -> str:
    """Decrypt base64-encoded ciphertext, return plaintext string."""
    ciphertext = base64.b64decode(ciphertext_b64)
    iv = base64.b64decode(iv_b64)
    tag = base64.b64decode(tag_b64)
    plaintext = aes_decrypt(key, ciphertext, iv, tag)
    return plaintext.decode("utf-8")


def secure_wipe(data) -> None:
    """
    Overwrite data with zeros to prevent memory leaks. # [REAL for bytearray/memoryview]
    Note: Python immutable types (bytes, str) cannot be wiped in place.
    For mutable types (bytearray), this does an actual in-place wipe.
    """
    if isinstance(data, bytearray):
        for i in range(len(data)):
            data[i] = 0
    elif isinstance(data, dict):
        for k in list(data.keys()):
            secure_wipe(data[k])
            data[k] = None
    # bytes/str are immutable — best we can do is delete reference
    del data
