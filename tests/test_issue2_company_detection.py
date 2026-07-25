import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from redactor import PIIRedactor

def test_issue2_valid_company_names_detected():
    redactor = PIIRedactor()
    valid_companies = [
        "Acme Innovations Private Limited",
        "TechCorp Ltd.",
        "Global Solutions Inc.",
        "Apex Enterprises Corp",
        "Pinnacle Systems Ltd"
    ]
    for comp in valid_companies:
        text = f"The contract was signed with {comp}."
        detected = redactor.detect_entities(text)
        company_spans = [d["text"] for d in detected if d["type"] == "COMPANY_NAME"]
        assert len(company_spans) > 0, f"Expected '{comp}' to be detected as COMPANY_NAME"

def test_issue2_generic_legal_phrases_not_detected_as_company():
    redactor = PIIRedactor()
    generic_phrases = [
        "Corporate Office",
        "Banking Regulation Act",
        "Securities and Exchange Board of India",
        "Corporate Governance Committee"
    ]
    for phrase in generic_phrases:
        text = f"The {phrase} issued guidelines."
        detected = redactor.detect_entities(text)
        company_spans = [d["text"] for d in detected if d["type"] == "COMPANY_NAME"]
        assert len(company_spans) == 0, f"False positive COMPANY_NAME detected for '{phrase}': {detected}"
