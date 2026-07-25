import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from redactor import PIIRedactor

def test_issue5_context_validation_valid_and_invalid():
    redactor = PIIRedactor()
    
    # Valid PII
    valid_text = "Contact Mr. Rajesh Kumar at +91 9876543210 or visit Acme Innovations Pvt. Ltd."
    valid_detected = redactor.detect_entities(valid_text)
    assert len(valid_detected) >= 3, "Expected valid PII entities to pass validation"

    # Invalid candidate spans (isolated words, invalid cards, unformatted numbers)
    invalid_text = "Call 12345 or visit Acme regarding Section 14"
    invalid_detected = redactor.detect_entities(invalid_text)
    types_detected = [d["type"] for d in invalid_detected]
    assert "PHONE_NUMBER" not in types_detected, "Short number 12345 should fail validation"
    assert "COMPANY_NAME" not in types_detected, "Bare word 'Acme' without suffix should fail validation"
