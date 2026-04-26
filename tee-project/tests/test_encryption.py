"""
Tests for backend/core/encryption.py
"""
import sys
import os
import base64
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from core.encryption import (
    generate_rsa_keypair,
    export_public_key_pem,
    export_private_key_pem,
    import_public_key_pem,
    import_private_key_pem,
    encrypt_with_rsa,
    decrypt_with_rsa,
    generate_session_key,
    aes_encrypt,
    aes_decrypt,
    aes_encrypt_b64,
    aes_decrypt_b64,
    secure_wipe,
)


class TestRSAKeyPair:
    def test_generate_returns_tuple(self):
        priv, pub = generate_rsa_keypair(bits=1024)
        assert priv is not None
        assert pub is not None

    def test_public_key_differs_from_private(self):
        priv, pub = generate_rsa_keypair(bits=1024)
        priv_pem = export_private_key_pem(priv)
        pub_pem = export_public_key_pem(pub)
        assert "PRIVATE" in priv_pem
        assert "PUBLIC" in pub_pem
        assert priv_pem != pub_pem

    def test_pem_round_trip(self):
        priv, pub = generate_rsa_keypair(bits=1024)
        pub_pem = export_public_key_pem(pub)
        priv_pem = export_private_key_pem(priv)
        reimported_pub = import_public_key_pem(pub_pem)
        reimported_priv = import_private_key_pem(priv_pem)
        assert export_public_key_pem(reimported_pub) == pub_pem
        assert export_private_key_pem(reimported_priv) == priv_pem


class TestRSAEncryptDecrypt:
    def setup_method(self):
        self.priv, self.pub = generate_rsa_keypair(bits=1024)

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = b"Hello, TEE World!"
        ciphertext = encrypt_with_rsa(self.pub, plaintext)
        recovered = decrypt_with_rsa(self.priv, ciphertext)
        assert recovered == plaintext

    def test_ciphertext_differs_from_plaintext(self):
        plaintext = b"secret data"
        ciphertext = encrypt_with_rsa(self.pub, plaintext)
        assert ciphertext != plaintext

    def test_ciphertext_length_equals_key_size(self):
        # RSA-1024 ciphertext is 128 bytes
        plaintext = b"test"
        ciphertext = encrypt_with_rsa(self.pub, plaintext)
        assert len(ciphertext) == 128

    def test_different_encryptions_produce_different_ciphertexts(self):
        # OAEP uses random padding, so same plaintext → different ciphertext
        plaintext = b"same plaintext"
        c1 = encrypt_with_rsa(self.pub, plaintext)
        c2 = encrypt_with_rsa(self.pub, plaintext)
        assert c1 != c2


class TestSessionKey:
    def test_generates_32_bytes(self):
        key = generate_session_key()
        assert len(key) == 32

    def test_keys_are_random(self):
        k1 = generate_session_key()
        k2 = generate_session_key()
        assert k1 != k2


class TestAESGCM:
    def setup_method(self):
        self.key = generate_session_key()

    def test_encrypt_returns_ciphertext_iv_tag(self):
        result = aes_encrypt(self.key, b"hello")
        assert "ciphertext" in result
        assert "iv" in result
        assert "tag" in result

    def test_iv_is_12_bytes(self):
        result = aes_encrypt(self.key, b"hello")
        assert len(result["iv"]) == 12

    def test_tag_is_16_bytes(self):
        result = aes_encrypt(self.key, b"hello")
        assert len(result["tag"]) == 16

    def test_roundtrip(self):
        plaintext = b"This is a secret message inside the TEE enclave."
        encrypted = aes_encrypt(self.key, plaintext)
        decrypted = aes_decrypt(self.key, encrypted["ciphertext"], encrypted["iv"], encrypted["tag"])
        assert decrypted == plaintext

    def test_wrong_key_raises(self):
        encrypted = aes_encrypt(self.key, b"secret")
        wrong_key = generate_session_key()
        with pytest.raises(Exception):
            aes_decrypt(wrong_key, encrypted["ciphertext"], encrypted["iv"], encrypted["tag"])

    def test_tampered_tag_raises(self):
        encrypted = aes_encrypt(self.key, b"secret")
        bad_tag = bytes([b ^ 0xFF for b in encrypted["tag"]])
        with pytest.raises(Exception):
            aes_decrypt(self.key, encrypted["ciphertext"], encrypted["iv"], bad_tag)

    def test_empty_plaintext(self):
        encrypted = aes_encrypt(self.key, b"")
        decrypted = aes_decrypt(self.key, encrypted["ciphertext"], encrypted["iv"], encrypted["tag"])
        assert decrypted == b""


class TestAESGCMBase64:
    def setup_method(self):
        self.key = generate_session_key()

    def test_encrypt_returns_b64_strings(self):
        result = aes_encrypt_b64(self.key, "hello world")
        # Should be valid base64
        base64.b64decode(result["ciphertext"])
        base64.b64decode(result["iv"])
        base64.b64decode(result["tag"])

    def test_roundtrip(self):
        original = "Privacy-preserving LLM inference with TEE"
        encrypted = aes_encrypt_b64(self.key, original)
        decrypted = aes_decrypt_b64(self.key, encrypted["ciphertext"], encrypted["iv"], encrypted["tag"])
        assert decrypted == original

    def test_unicode_roundtrip(self):
        original = "Hello \u4e16\u754c TEE \U0001f512"  # Hello World TEE (with unicode + emoji)
        encrypted = aes_encrypt_b64(self.key, original)
        decrypted = aes_decrypt_b64(self.key, encrypted["ciphertext"], encrypted["iv"], encrypted["tag"])
        assert decrypted == original


class TestSecureWipe:
    def test_bytearray_wiped(self):
        data = bytearray(b"secret key material 12345")
        secure_wipe(data)
        assert all(b == 0 for b in data)

    def test_dict_wiped(self):
        data = {"key": bytearray(b"secret"), "other": bytearray(b"value")}
        secure_wipe(data)
        # After wipe all values should be None or zero
        for v in data.values():
            assert v is None or (isinstance(v, bytearray) and all(b == 0 for b in v))
