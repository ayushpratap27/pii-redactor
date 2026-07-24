import re
import random
from typing import List, Dict
from stdnum import luhn
import phonenumbers
from faker import Faker
import spacy

class PIIRedactor:
    """High-precision, layout-preserving PII detector and consistent anonymizer."""

    NON_PII_WORDS = {
        "TABLE OF CONTENTS", "SECTION I", "RED HERRING PROSPECTUS", "COMPANIES ACT",
        "FRESH ISSUE", "OFFER FOR SALE", "REGISTERED OFFICE", "CORPORATE OFFICE",
        "CONTACT PERSON", "EQUITY SHARES", "BOOK BUILT OFFER", "GENERAL INFORMATION",
        "PAGE", "DETAILS OF THE OFFER", "TOTAL OFFER SIZE", "ELIGIBILITY",
        "STATEMENT OF", "FINANCIAL STATEMENTS", "BOARD OF DIRECTORS", "RISK FACTORS",
        "TAX ID", "SSN", "DOB", "IP", "CREDIT CARD", "TELEPHONE", "EMAIL", "WEBSITE"
    }

    def __init__(self, seed: int = 42):
        self.fake = Faker("en_US")
        Faker.seed(seed)
        random.seed(seed)
        self.entity_map: Dict[str, str] = {}

        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            self.nlp = spacy.blank("en")

        # Compile regexes
        self.email_re = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', re.I)
        self.ssn_re = re.compile(r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b')
        self.pan_re = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
        self.card_re = re.compile(r'\b(?:\d[ -]*?){13,19}\b')
        self.date_re = re.compile(
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b|\b(?:19|20)\d{2}[-/.] (?:0[1-9]|1[0-2])[-/.] (?:0[1-9]|[12]\d|3[01])\b',
            re.I
        )
        self.ip_re = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
        self.cin_re = re.compile(r'\b[U|L]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b')
        self.din_re = re.compile(r'\b(?:DIN|DIN:)\s*\d{8}\b', re.I)
        self.promoter_re = re.compile(r'OUR PROMOTERS:\s*([^.\n]+)', re.I)
        self.address_re = re.compile(r'(?:REGISTERED OFFICE|CORPORATE OFFICE):\s*([^.\n]+)', re.I)

    def detect_entities(self, text: str) -> List[Dict]:
        if not text or not text.strip():
            return []

        regex_spans = []

        # 1. Emails
        for m in self.email_re.finditer(text):
            regex_spans.append({"start": m.start(), "end": m.end(), "text": m.group(), "type": "EMAIL", "priority": 10})

        # 2. Phone Numbers
        for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
            regex_spans.append({"start": match.start, "end": match.end, "text": match.raw_string, "type": "PHONE_NUMBER", "priority": 9})

        phone_in_re = re.compile(r'\b(?:\+?\s*91[\s.-]?)?(?:[6-9]\d{9}|[2-9]\d{1,4}[\s.-]?\d{6,8})\b')
        for m in phone_in_re.finditer(text):
            raw = m.group()
            if len(re.sub(r'\D', '', raw)) >= 10:
                regex_spans.append({"start": m.start(), "end": m.end(), "text": raw, "type": "PHONE_NUMBER", "priority": 9})

        # 3. SSN / PAN
        for m in self.ssn_re.finditer(text):
            regex_spans.append({"start": m.start(), "end": m.end(), "text": m.group(), "type": "SSN_TAX_ID", "priority": 10})
        for m in self.pan_re.finditer(text):
            regex_spans.append({"start": m.start(), "end": m.end(), "text": m.group(), "type": "SSN_TAX_ID", "priority": 10})

        # 4. Credit Cards
        for m in self.card_re.finditer(text):
            digits = re.sub(r'\D', '', m.group())
            if 13 <= len(digits) <= 19 and luhn.is_valid(digits):
                regex_spans.append({"start": m.start(), "end": m.end(), "text": m.group(), "type": "CREDIT_CARD", "priority": 10})

        # 5. Dates
        for m in self.date_re.finditer(text):
            regex_spans.append({"start": m.start(), "end": m.end(), "text": m.group(), "type": "DATE_OF_BIRTH", "priority": 8})

        # 6. IP Addresses
        for m in self.ip_re.finditer(text):
            regex_spans.append({"start": m.start(), "end": m.end(), "text": m.group(), "type": "IP_ADDRESS", "priority": 10})

        # 7. CIN / DIN
        for m in self.cin_re.finditer(text):
            regex_spans.append({"start": m.start(), "end": m.end(), "text": m.group(), "type": "CIN_DIN", "priority": 10})
        for m in self.din_re.finditer(text):
            regex_spans.append({"start": m.start(), "end": m.end(), "text": m.group(), "type": "CIN_DIN", "priority": 10})

        # 8. Address Context Heuristic
        m_addr = self.address_re.search(text)
        if m_addr:
            raw_addr = m_addr.group(1).strip()
            idx = text.find(raw_addr, m_addr.start(1))
            if idx != -1:
                regex_spans.append({"start": idx, "end": idx + len(raw_addr), "text": raw_addr, "type": "ADDRESS", "priority": 9})

        # 9. Promoters Context Heuristic
        m_prom = self.promoter_re.search(text)
        if m_prom:
            names_raw = m_prom.group(1)
            offset = m_prom.start(1)
            for item in re.split(r',|\bAND\b', names_raw):
                clean = item.strip()
                if clean and len(clean.split()) >= 2 and clean.isupper() and "TRUST" not in clean and "LIMITED" not in clean:
                    idx = text.find(clean, offset)
                    if idx != -1:
                        regex_spans.append({"start": idx, "end": idx + len(clean), "text": clean, "type": "FULL_NAME", "priority": 9})

        # 10. NER Spans (Lower priority)
        ner_spans = []
        doc = self.nlp(text)
        for ent in doc.ents:
            ent_txt_upper = ent.text.strip().upper()
            if any(non_pii in ent_txt_upper for non_pii in self.NON_PII_WORDS):
                continue
            if ent.label_ == "PERSON" and len(ent.text.strip()) > 2:
                # Discard PERSON tags that contain SSN or TAX ID
                if not any(kw in ent_txt_upper for kw in ["SSN", "TAX", "ID", "TALUKA"]):
                    ner_spans.append({"start": ent.start_char, "end": ent.end_char, "text": ent.text, "type": "FULL_NAME", "priority": 5})
            elif ent.label_ == "ORG" and len(ent.text.strip()) > 3:
                if any(kw in ent.text.upper() for kw in ["LTD", "LIMITED", "INC", "CORP", "BANK", "SECURITIES", "TRUST"]):
                    ner_spans.append({"start": ent.start_char, "end": ent.end_char, "text": ent.text, "type": "COMPANY_NAME", "priority": 5})

        all_spans = regex_spans + ner_spans
        return self._resolve_overlaps(all_spans)

    def _resolve_overlaps(self, spans: List[Dict]) -> List[Dict]:
        if not spans:
            return []
        # Sort by priority DESC, then by span length DESC
        sorted_spans = sorted(spans, key=lambda s: (-s.get("priority", 1), -(s["end"] - s["start"]), s["start"]))
        resolved = []
        for s in sorted_spans:
            if not any(max(s["start"], r["start"]) < min(s["end"], r["end"]) for r in resolved):
                resolved.append(s)
        return sorted(resolved, key=lambda s: s["start"])

    def get_replacement(self, entity_text: str, entity_type: str) -> str:
        key = entity_text.strip().lower()
        if key in self.entity_map:
            return self.entity_map[key]

        if entity_type == "FULL_NAME":
            synthetic = self.fake.name().upper() if entity_text.isupper() else self.fake.name()
        elif entity_type == "EMAIL":
            synthetic = f"{self.fake.first_name().lower()}.{self.fake.last_name().lower()}@example.com"
        elif entity_type == "PHONE_NUMBER":
            synthetic = f"+91 98{random.randint(10000000, 99999999)}"
        elif entity_type == "COMPANY_NAME":
            synthetic = self.fake.company().upper() if entity_text.isupper() else self.fake.company()
        elif entity_type == "ADDRESS":
            synthetic = f"{random.randint(10, 99)}, {self.fake.street_name()}, {self.fake.city()} - {random.randint(100000, 999999)}, India"
        elif entity_type == "SSN_TAX_ID":
            synthetic = f"ABCDE{random.randint(1000, 9999)}K" if len(entity_text) == 10 else f"9{random.randint(10, 99)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        elif entity_type == "CREDIT_CARD":
            synthetic = self.fake.credit_card_number()
        elif entity_type == "DATE_OF_BIRTH":
            synthetic = "January 15, 2001" if any(m in entity_text for m in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]) else "2001-01-15"
        elif entity_type == "IP_ADDRESS":
            synthetic = f"192.0.2.{random.randint(1, 254)}"
        elif entity_type == "CIN_DIN":
            synthetic = f"DIN: {random.randint(10000000, 99999999)}" if "DIN" in entity_text.upper() else f"U{random.randint(10000, 99999)}MH2000PLC{random.randint(100000, 999999)}"
        else:
            synthetic = f"[REDACTED_{entity_type}]"

        self.entity_map[key] = synthetic
        return synthetic
