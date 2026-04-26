"""
Privacy analysis — detects PII in text and returns a privacy score.
# [REAL] Regex-based PII detection
"""
import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class PrivacyReport:
    score: float          # 0 (high PII) to 100 (no PII)
    pii_detected: List[str] = field(default_factory=list)
    risk_level: str = "LOW"
    details: dict = field(default_factory=dict)


# PII regex patterns
_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "phone_us": re.compile(r"\b(\+1[\s\-]?)?(\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ \-]?){13,16}\b"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "date_of_birth": re.compile(r"\b(dob|date of birth|born on)[:\s]+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", re.I),
    "passport": re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),
    "name_pattern": re.compile(r"\b(my name is|i am|i'm)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", re.I),
}

# Weight each PII type by severity (higher = worse for score)
_WEIGHTS = {
    "ssn": 40,
    "credit_card": 35,
    "passport": 30,
    "email": 20,
    "phone_us": 15,
    "date_of_birth": 15,
    "ipv4": 10,
    "name_pattern": 10,
}


def analyze_privacy(text: str) -> PrivacyReport:
    """
    Analyze text for PII and return a PrivacyReport.
    Score 100 = completely clean; 0 = maximum PII risk.
    """
    if not text or not text.strip():
        return PrivacyReport(score=100.0, pii_detected=[], risk_level="NONE")

    detected = []
    details = {}
    total_penalty = 0

    for pii_type, pattern in _PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            detected.append(pii_type)
            count = len(matches)
            details[pii_type] = count
            penalty = _WEIGHTS.get(pii_type, 10) * count
            total_penalty += penalty

    # Clamp score between 0 and 100
    score = max(0.0, min(100.0, 100.0 - total_penalty))

    if score >= 80:
        risk_level = "LOW"
    elif score >= 50:
        risk_level = "MEDIUM"
    elif score >= 20:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    return PrivacyReport(
        score=round(score, 1),
        pii_detected=detected,
        risk_level=risk_level,
        details=details,
    )
