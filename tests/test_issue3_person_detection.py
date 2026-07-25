import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from redactor import PIIRedactor

def test_issue3_full_names_with_honorifics_detected():
    redactor = PIIRedactor()
    honorific_names = [
        ("Mr. Rajesh Kumar", "Rajesh Kumar"),
        ("Shri Amit Sharma", "Amit Sharma"),
        ("Dr. Sunita Patel", "Sunita Patel"),
        ("Smt. Anita Verma", "Anita Verma")
    ]
    for full_phrase, expected_name in honorific_names:
        text = f"The report was prepared by {full_phrase} for review."
        detected = redactor.detect_entities(text)
        name_spans = [d["text"] for d in detected if d["type"] == "FULL_NAME"]
        assert expected_name in name_spans, f"Expected '{expected_name}' to be fully detected in '{text}', got {name_spans}"

def test_issue3_standalone_titles_not_detected_as_person():
    redactor = PIIRedactor()
    standalone_titles = ["Director", "Secretary", "Statutory Auditor", "Manager", "Notice", "Statement"]
    for title in standalone_titles:
        text = f"The {title} signed the document."
        detected = redactor.detect_entities(text)
        person_spans = [d["text"] for d in detected if d["type"] == "FULL_NAME"]
        assert title not in person_spans, f"False positive FULL_NAME detected for standalone title '{title}'"
