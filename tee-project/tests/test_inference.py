"""
Tests for nonce tracker, rate limiter, and privacy analyzer.
(Integration tests for inference logic without needing FastAPI server running)
"""
import sys
import os
import time
import uuid
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from utils.nonce_tracker import NonceTracker
from utils.rate_limiter import RateLimiter
from utils.privacy_analyzer import analyze_privacy, PrivacyReport
from core.llm import DummyLLM, infer


class TestNonceTracker:
    def test_new_nonce_is_valid(self):
        tracker = NonceTracker()
        nonce = str(uuid.uuid4())
        assert tracker.is_valid(nonce) is True

    def test_used_nonce_is_invalid(self):
        tracker = NonceTracker()
        nonce = str(uuid.uuid4())
        tracker.add(nonce)
        assert tracker.is_valid(nonce) is False

    def test_size_increments(self):
        tracker = NonceTracker()
        assert tracker.size == 0
        tracker.add("nonce-1")
        tracker.add("nonce-2")
        assert tracker.size == 2

    def test_expired_nonces_cleaned(self):
        tracker = NonceTracker(ttl_seconds=1)
        tracker.add("old-nonce")
        assert tracker.size == 1
        time.sleep(1.1)
        tracker.cleanup_expired()
        assert tracker.size == 0

    def test_different_nonces_both_valid(self):
        tracker = NonceTracker()
        n1 = str(uuid.uuid4())
        n2 = str(uuid.uuid4())
        assert tracker.is_valid(n1) is True
        assert tracker.is_valid(n2) is True
        tracker.add(n1)
        assert tracker.is_valid(n1) is False
        assert tracker.is_valid(n2) is True


class TestRateLimiter:
    def test_allows_under_limit(self):
        limiter = RateLimiter(limit=5, window_seconds=60)
        for _ in range(5):
            assert limiter.is_allowed("127.0.0.1") is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter(limit=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("10.0.0.1")
        assert limiter.is_allowed("10.0.0.1") is False

    def test_different_ips_independent(self):
        limiter = RateLimiter(limit=2, window_seconds=60)
        limiter.is_allowed("1.1.1.1")
        limiter.is_allowed("1.1.1.1")
        assert limiter.is_allowed("1.1.1.1") is False
        assert limiter.is_allowed("2.2.2.2") is True

    def test_stats_contains_required_fields(self):
        limiter = RateLimiter()
        stats = limiter.get_stats()
        assert "tracked_ips" in stats
        assert "total_violations" in stats
        assert "limit_per_window" in stats
        assert "window_seconds" in stats

    def test_violations_counted(self):
        limiter = RateLimiter(limit=1, window_seconds=60)
        limiter.is_allowed("9.9.9.9")
        limiter.is_allowed("9.9.9.9")  # violation
        limiter.is_allowed("9.9.9.9")  # violation
        assert limiter.get_stats()["total_violations"] == 2


class TestPrivacyAnalyzer:
    def test_clean_text_scores_100(self):
        report = analyze_privacy("What is the capital of France?")
        assert report.score == 100.0
        assert report.risk_level == "LOW"
        assert report.pii_detected == []

    def test_email_detected(self):
        report = analyze_privacy("Contact me at alice@example.com for details.")
        assert "email" in report.pii_detected
        assert report.score < 100.0

    def test_ssn_detected_critical(self):
        report = analyze_privacy("My SSN is 123-45-6789")
        assert "ssn" in report.pii_detected
        assert report.risk_level in ("CRITICAL", "HIGH")

    def test_credit_card_detected(self):
        report = analyze_privacy("Card: 4111111111111111")
        assert "credit_card" in report.pii_detected

    def test_empty_text_returns_100(self):
        report = analyze_privacy("")
        assert report.score == 100.0
        assert report.risk_level == "NONE"

    def test_whitespace_only_returns_100(self):
        report = analyze_privacy("   \n\t  ")
        assert report.score == 100.0

    def test_multiple_pii_lower_score(self):
        # Email + phone + SSN should score lower than just email
        report_single = analyze_privacy("Email: user@test.com")
        report_multi = analyze_privacy("Email: user@test.com, SSN: 123-45-6789, Card: 4111111111111111")
        assert report_multi.score < report_single.score

    def test_report_is_privacy_report_instance(self):
        report = analyze_privacy("hello world")
        assert isinstance(report, PrivacyReport)

    def test_risk_level_low_for_clean(self):
        report = analyze_privacy("Tell me about machine learning algorithms.")
        assert report.risk_level == "LOW"

    def test_score_clamped_to_zero(self):
        # Extreme PII should not go below 0
        text = "SSN: 123-45-6789. Card: 4111111111111111. Email: a@b.com. Passport: AB1234567"
        report = analyze_privacy(text)
        assert report.score >= 0.0
        assert report.score <= 100.0


class TestDummyLLM:
    def setup_method(self):
        self.llm = DummyLLM()

    def test_hello_response(self):
        response = self.llm.infer("hello", "dummy", 512)
        assert "Trusted Execution Environment" in response

    def test_tee_response(self):
        response = self.llm.infer("explain TEE please", "dummy", 512)
        assert "TEE" in response or "Trusted" in response

    def test_privacy_response(self):
        response = self.llm.infer("tell me about privacy", "dummy", 512)
        assert len(response) > 20

    def test_default_response_contains_hash(self):
        response = self.llm.infer("some random query xyz123", "dummy", 512)
        assert "hash:" in response

    def test_infer_returns_string(self):
        response = self.llm.infer("test query", "dummy", 100)
        assert isinstance(response, str)
        assert len(response) > 0


class TestInferFunction:
    def test_infer_returns_string(self):
        result = infer("hello world", model="dummy", max_tokens=100)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_infer_enclave_clears_after_use(self):
        from core.enclave import get_enclave
        result = infer("test prompt for enclave isolation", model="dummy")
        # After enclave context exits, isolated memory should be cleared
        enclave = get_enclave()
        assert not enclave._active  # should not be active between calls
        assert len(enclave._isolated_memory) == 0  # memory wiped
