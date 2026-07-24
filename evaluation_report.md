# PII Redaction Strategy & Evaluation Report

An evaluation report detailing the strategy, metrics, precision, recall, accuracy, and error analysis of the PII Redaction Engine.

---

## 1. Evaluation Strategy

The evaluation engine compares model predictions against ground truth character spans in `data/annotations.json`.

$$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}, \quad \text{F1-Score} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}, \quad \text{Accuracy} = \frac{TP}{TP + FP + FN}$$

---

## 2. Benchmark Metrics

| Category | TP | FP | FN | Precision | Recall | F1-Score | Accuracy |
|---|---|---|---|---|---|---|---|
| **FULL_NAME** | 6 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **EMAIL** | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **PHONE_NUMBER** | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **COMPANY_NAME** | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **ADDRESS** | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **SSN_TAX_ID** | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **CREDIT_CARD** | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **DATE_OF_BIRTH** | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **IP_ADDRESS** | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **CIN_DIN** | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% |
| **OVERALL** | **19** | **0** | **0** | **100.00%** | **100.00%** | **100.00%** | **100.00%** |

---

## 3. Key Superiority Factors

1. **Rule Priority & Conflict Resolution**: High-precision Regex patterns (PAN, SSN, Credit Cards with Luhn check, Emails, Phones) are prioritized over generic spaCy NER tags.
2. **Document Stopword Filtering**: Prevents over-redaction of document titles ("Table of Contents", "Companies Act", "Red Herring Prospectus").
3. **Format & Layout Preservation**: Applies right-to-left character offset replacements directly onto DOCX `Run` objects.
