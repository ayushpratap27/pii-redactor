import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from redactor import PIIRedactor

def test_issue1_legal_and_financial_false_positives():
    redactor = PIIRedactor()
    
    test_terms = [
        "Offer",
        "Issue",
        "Book Building Process",
        "Companies Act",
        "Registrar of Companies",
        "SEBI",
        "BSE",
        "NSE",
        "Risk Factors",
        "Stock Exchanges"
    ]
    
    for term in test_terms:
        text = f"The {term} was conducted under regulatory guidelines."
        detected = redactor.detect_entities(text)
        detected_texts = [d["text"] for d in detected]
        assert term not in detected_texts, f"False positive detected for term '{term}' in: '{text}'"

def test_issue1_complex_legal_sentence():
    redactor = PIIRedactor()
    sample_text = (
        "SEBI and BSE approved the Book Building Process under the Companies Act "
        "for the Fresh Issue and Offer for Sale registered with the Registrar of Companies."
    )
    detected = redactor.detect_entities(sample_text)
    assert len(detected) == 0, f"Expected 0 detections in legal terms text, but got: {detected}"
