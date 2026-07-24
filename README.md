# PII Redaction Tool

A high-precision Python application designed to detect Personally Identifiable Information (PII), anonymize text with consistent synthetic replacements, and evaluate detection performance inside Microsoft Word (`.docx`) documents while preserving 100% of document styling, table structures, and formatting layout.

---

## 📌 Approach & Technical Architecture

This solution combines a **Hybrid Extraction Pipeline**, **Deterministic Consistent Anonymization Mapping**, and a **Format-Preserving DOCX AST Engine**:

1. **Hybrid Detection Engine**:
   - **Regex & Pattern Extractors**: RFC 5322 Email regex, Google `phonenumbers` + Indian number formats (`+91`), US SSN (`XXX-XX-XXXX`), Indian PAN (`ABCDE1234F`), Credit Cards (with mandatory Luhn algorithm verification via `python-stdnum`), IPv4 addresses, Dates of Birth, and Corporate Identity Numbers (CIN/DIN).
   - **NER Model & Heuristics**: `spaCy` (`en_core_web_sm`) for `PERSON` (Full Names), `ORG` (Company Names), and `GPE`/`LOC`/`FAC` (Physical Addresses), augmented with custom document context heuristics (Promoter lists, Officer titles).
   - **Disambiguation & Overlap Resolution**: Overlapping entity spans are resolved by prioritizing confidence scores, span lengths, and deterministic patterns over generic NER models.

2. **Deterministic Synthetic Anonymization**:
   - Uses `Faker` to generate realistic, format-preserving synthetic replacement values (e.g. `John Doe` -> `Michael Anderson`, `john.doe@gmail.com` -> `michael.anderson@example.org`, `+91 9876543210` -> `+91 9812345678`, `March 20, 2025` -> `October 11, 1991`).
   - Maintains a global lookup map to ensure that **every repeated instance of the exact same entity receives the exact same synthetic replacement** throughout body paragraphs, tables, headers, and footers.

3. **Format & Layout Preservation**:
   - Modifies Microsoft Word (`.docx`) DOM at the `Run` object level right-to-left based on character-span offsets.
   - Preserves inline styles (`bold`, `italic`, `font family`, `font color`, `font size`), cell borders, and document alignment without breaking XML elements.

---

## 🎯 Supported PII Categories

| PII Category | Detection Method | Validation / Heuristic |
|---|---|---|
| **Full Names** | `spaCy` NER (`PERSON`) + Context Rules | Title context & case-matched synthetic replacements |
| **Email Addresses** | RFC 5322 Regex | Pattern matching |
| **Phone Numbers** | `phonenumbers` + Indian (+91) Regex | Country code, STD code & digit count verification |
| **Company Names** | `spaCy` NER (`ORG`) + Regex | Corporate suffix filter |
| **Physical Addresses** | `spaCy` NER (`GPE`, `LOC`, `FAC`) + Regex | Address keyword heuristics |
| **SSN / Tax IDs** | Regex + Format Rules | US SSN area code checks & Indian PAN pattern |
| **Credit Card Numbers** | Regex + Luhn Algorithm | Mandatory Luhn checksum validation |
| **Dates of Birth** | Regex (ISO, US, Textual) | Format-preserving synthetic date generator |
| **IP Addresses** | IPv4 Regex | Octet numeric boundary checks (`0-255`) |
| **CIN / DIN** | Regulatory Regex | 21-digit CIN & 8-digit DIN extraction |

---

## 🛠️ Installation & Usage

### 1. Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Command Line Interface (CLI)
```bash
# Redact document
python main.py "sample_document.docx" "redacted_document.docx"

# Redact and run benchmark evaluation against ground truth annotations
python main.py "sample_document.docx" "redacted_document.docx" --annotation data/annotations.json --evaluate
```

### 3. Interactive Web Application
```bash
streamlit run app.py
```

---

## 📊 Evaluation Report

For complete precision, recall, F1-score, and category-level evaluation details, see [`evaluation_report.md`](evaluation_report.md).
