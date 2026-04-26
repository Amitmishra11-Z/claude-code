"""
Tests for backend/core/attestation.py
"""
import sys
import os
import json
import base64
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from core.attestation import generate_quote, verify_quote, get_attestation_report
from core.enclave import initialize_enclave, get_enclave


class TestGenerateQuote:
    def setup_method(self):
        initialize_enclave()

    def test_returns_base64_string(self):
        quote = generate_quote({"test": "data"})
        assert isinstance(quote, str)
        # Should be valid base64
        decoded = base64.b64decode(quote)
        assert len(decoded) > 0

    def test_quote_contains_required_fields(self):
        quote = generate_quote({"purpose": "test"})
        decoded = json.loads(base64.b64decode(quote))
        assert "version" in decoded
        assert "mrenclave" in decoded
        assert "mrsigner" in decoded
        assert "timestamp" in decoded
        assert "report_data" in decoded

    def test_quote_version_is_1(self):
        quote = generate_quote({})
        decoded = json.loads(base64.b64decode(quote))
        assert decoded["version"] == 1

    def test_quote_type_is_simulated(self):
        quote = generate_quote({})
        decoded = json.loads(base64.b64decode(quote))
        assert "SIMULATED" in decoded["type"]

    def test_quote_timestamp_is_recent(self):
        before = time.time()
        quote = generate_quote({})
        after = time.time()
        decoded = json.loads(base64.b64decode(quote))
        assert before <= decoded["timestamp"] <= after

    def test_different_data_produces_different_report_hash(self):
        q1 = generate_quote({"data": "value1"})
        q2 = generate_quote({"data": "value2"})
        d1 = json.loads(base64.b64decode(q1))
        d2 = json.loads(base64.b64decode(q2))
        assert d1["report_data"] != d2["report_data"]

    def test_nonces_are_unique(self):
        q1 = generate_quote({"x": 1})
        q2 = generate_quote({"x": 1})
        d1 = json.loads(base64.b64decode(q1))
        d2 = json.loads(base64.b64decode(q2))
        assert d1["nonce"] != d2["nonce"]


class TestVerifyQuote:
    def setup_method(self):
        initialize_enclave()

    def test_valid_fresh_quote_passes(self):
        quote = generate_quote({"purpose": "test"})
        assert verify_quote(quote) is True

    def test_invalid_base64_fails(self):
        assert verify_quote("not-valid-base64!!!") is False

    def test_empty_string_fails(self):
        assert verify_quote("") is False

    def test_missing_fields_fails(self):
        # Encode a JSON object with missing required fields
        partial = json.dumps({"version": 1, "mrenclave": "abc"})
        bad_quote = base64.b64encode(partial.encode()).decode()
        assert verify_quote(bad_quote) is False

    def test_stale_quote_fails(self):
        # Create a quote with an old timestamp
        enclave = get_enclave()
        old_payload = {
            "version": 1,
            "type": "SIMULATED_SGX_QUOTE",
            "mrenclave": enclave.mrenclave,
            "mrsigner": enclave.mrsigner,
            "timestamp": time.time() - 7200,  # 2 hours ago
            "nonce": "deadbeef",
            "report_data": "abc123",
        }
        stale_quote = base64.b64encode(json.dumps(old_payload).encode()).decode()
        assert verify_quote(stale_quote) is False

    def test_fresh_quote_within_1_hour_passes(self):
        enclave = get_enclave()
        fresh_payload = {
            "version": 1,
            "type": "SIMULATED_SGX_QUOTE",
            "mrenclave": enclave.mrenclave,
            "mrsigner": enclave.mrsigner,
            "timestamp": time.time() - 1800,  # 30 minutes ago
            "nonce": "freshbeef",
            "report_data": "abc123",
        }
        fresh_quote = base64.b64encode(json.dumps(fresh_payload).encode()).decode()
        assert verify_quote(fresh_quote) is True


class TestGetAttestationReport:
    def setup_method(self):
        initialize_enclave()

    def test_returns_dict(self):
        report = get_attestation_report()
        assert isinstance(report, dict)

    def test_contains_required_fields(self):
        report = get_attestation_report()
        required = {"mrenclave", "mrsigner", "timestamp", "trust_level", "quote", "platform_info"}
        assert required.issubset(report.keys())

    def test_trust_level_is_simulated(self):
        report = get_attestation_report()
        assert report["trust_level"] == "SIMULATED"

    def test_quote_is_verifiable(self):
        report = get_attestation_report()
        assert verify_quote(report["quote"]) is True

    def test_platform_info_has_sgx_type(self):
        report = get_attestation_report()
        assert "sgx_type" in report["platform_info"]

    def test_timestamp_is_recent(self):
        before = time.time()
        report = get_attestation_report()
        after = time.time()
        assert before <= report["timestamp"] <= after

    def test_mrenclave_is_64_char_hex(self):
        report = get_attestation_report()
        mrenclave = report["mrenclave"]
        assert len(mrenclave) == 64
        # Should be valid hex
        int(mrenclave, 16)

    def test_advisory_present(self):
        report = get_attestation_report()
        assert "advisory" in report
        assert len(report["advisory"]) > 0
