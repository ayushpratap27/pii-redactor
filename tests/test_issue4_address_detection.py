import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from redactor import PIIRedactor

def test_issue4_addresses_with_abbreviations_detected():
    redactor = PIIRedactor()
    sample_text = "REGISTERED OFFICE: Plot No. 45, St. John Road, Mumbai - 400001, India. Tel: +91 9876543210"
    detected = redactor.detect_entities(sample_text)
    addr_spans = [d for d in detected if d["type"] == "ADDRESS"]
    assert len(addr_spans) > 0, "Expected address to be detected"
    addr_text = addr_spans[0]["text"]
    assert "Plot No. 45" in addr_text, f"Expected abbreviation 'Plot No.' inside detected address, got: '{addr_text}'"
    assert "Tel:" not in addr_text, f"Nearby label 'Tel:' was incorrectly included in address: '{addr_text}'"

def test_issue4_standalone_pincode_address_detected():
    redactor = PIIRedactor()
    sample_text = "The warehouse is located at 123 MG Road, Sector 4, Bengaluru - 560001."
    detected = redactor.detect_entities(sample_text)
    addr_spans = [d["text"] for d in detected if d["type"] == "ADDRESS"]
    assert len(addr_spans) > 0, "Expected standalone address with PIN code to be detected"
