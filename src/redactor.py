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
        "TAX ID", "SSN", "DOB", "IP", "CREDIT CARD", "TELEPHONE", "EMAIL", "WEBSITE",
        "OFFER", "ISSUE", "BOOK BUILDING PROCESS", "BOOK BUILDING", "REGISTRAR OF COMPANIES",
        "ROC", "SEBI", "BSE", "NSE", "STOCK EXCHANGES", "STOCK EXCHANGE",
        "RESERVE BANK OF INDIA", "RBI", "MINISTRY OF CORPORATE AFFAIRS", "MCA",
        "DRAFT RED HERRING PROSPECTUS", "DRHP", "RHP", "PROSPECTUS", "PROMOTER GROUP",
        "KEY MANAGERIAL PERSONNEL", "KMP", "STATUTORY AUDITOR", "AUDITOR'S REPORT",
        "NATIONAL STOCK EXCHANGE", "BOMBAY STOCK EXCHANGE", "DIRECTOR", "SECRETARY",
        "COMPLIANCE OFFICER", "COMPANY SECRETARY", "MANAGER", "CHAIRMAN", "MANAGING DIRECTOR",
        "CHIEF FINANCIAL OFFICER", "CFO", "CEO", "NOTICE", "STATEMENT", "SECTION"
    }

    def is_non_pii(self, text: str) -> bool:
        clean = re.sub(r'^\W+|\W+$', '', text.strip().upper())
        if not clean:
            return True
        if clean in self.NON_PII_WORDS:
            return True
        for non_pii in self.NON_PII_WORDS:
            if len(non_pii) > 3 and (clean == non_pii or f" {non_pii} " in f" {clean} "):
                return True
        return False

    def __init__(self, seed: int = 42):
        self.fake = Faker("en_US")
        Faker.seed(seed)
        random.seed(seed)
        self.entity_map: Dict[str, str] = {}

        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            try:
                import spacy.cli
                spacy.cli.download("en_core_web_sm")
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
        self.address_re = re.compile(
            r'(?:REGISTERED OFFICE|CORPORATE OFFICE):\s*([^\n\r]+?)(?=(?:\s+(?:Tel|Telephone|Email|Website|Fax|Contact|CIN|DIN):|\n|\r|$))',
            re.I
        )
        self.pincode_address_re = re.compile(
            r'\b(?:\d{1,4}[,\s]+[\w\s.,-]{5,100}[,\s]+(?:\d{6}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*-\s*\d{6}))\b'
        )
        self.company_suffix_re = re.compile(r'\b(?:PVT\.?|PRIVATE|LIMITED|LTD\.?|INC\.?|CORP\.?|CORPORATION|LLP|PLC)\b', re.I)
        self.honorific_name_re = re.compile(r'\b(?:Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Shri|Smt\.|Sri)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b')

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

        # 8. Address Context Heuristics
        m_addr = self.address_re.search(text)
        if m_addr:
            raw_addr = m_addr.group(1).strip()
            raw_addr = re.sub(r'[\s.,;-]+(?:Tel|Telephone|Email|Website|Fax|Contact|CIN|DIN):?.*$', '', raw_addr, flags=re.I).strip()
            if len(raw_addr) > 5:
                idx = text.find(raw_addr, m_addr.start(1))
                if idx != -1:
                    regex_spans.append({"start": idx, "end": idx + len(raw_addr), "text": raw_addr, "type": "ADDRESS", "priority": 9})

        for m in self.pincode_address_re.finditer(text):
            raw_addr = m.group(0).strip()
            if not self.is_non_pii(raw_addr) and len(raw_addr) > 10:
                regex_spans.append({"start": m.start(), "end": m.end(), "text": raw_addr, "type": "ADDRESS", "priority": 9})

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

        # 10. Honorific Names Context Extractor
        for m in self.honorific_name_re.finditer(text):
            name_part = m.group(1).strip()
            if not self.is_non_pii(name_part):
                regex_spans.append({"start": m.start(1), "end": m.end(1), "text": name_part, "type": "FULL_NAME", "priority": 9})

        # 11. NER Spans (Lower priority)
        ner_spans = []
        doc = self.nlp(text)
        for ent in doc.ents:
            if self.is_non_pii(ent.text):
                continue
            ent_txt_upper = ent.text.strip().upper()
            if ent.label_ == "PERSON" and len(ent.text.strip()) > 2:
                if not any(kw in ent_txt_upper for kw in ["SSN", "TAX", "ID", "TALUKA"]):
                    # Expand contiguous capitalized tokens to avoid partial name replacements
                    start = ent.start_char
                    end = ent.end_char
                    match_right = re.match(r'^(\s+[A-Z][a-zA-Z]+)', text[end:])
                    if match_right:
                        end += len(match_right.group(1))
                    full_name_candidate = text[start:end].strip()
                    if not self.is_non_pii(full_name_candidate):
                        ner_spans.append({"start": start, "end": end, "text": full_name_candidate, "type": "FULL_NAME", "priority": 5})
            elif ent.label_ == "ORG" and len(ent.text.strip()) > 3:
                if self.company_suffix_re.search(ent.text):
                    if not any(generic in ent_txt_upper for generic in ["CORPORATE OFFICE", "BANKING REGULATION", "CORPORATE GOVERNANCE", "REGISTRATION"]):
                        ner_spans.append({"start": ent.start_char, "end": ent.end_char, "text": ent.text, "type": "COMPANY_NAME", "priority": 5})

        all_spans = [s for s in (regex_spans + ner_spans) if not self.is_non_pii(s["text"])]
        return self._resolve_overlaps(all_spans)

    def _resolve_overlaps(self, spans: List[Dict]) -> List[Dict]:
        if not spans:
            return []
        sorted_spans = sorted(spans, key=lambda s: (-s.get("priority", 1), -(s["end"] - s["start"]), s["start"]))
        resolved = []
        for s in sorted_spans:
            if not any(max(s["start"], r["start"]) < min(s["end"], r["end"]) for r in resolved):
                resolved.append(s)
        return sorted(resolved, key=lambda s: s["start"])

    def _generate_synthetic_date(self, entity_text: str) -> str:
        fake_date = self.fake.date_of_birth(minimum_age=20, maximum_age=60)
        txt_lower = entity_text.lower()
        
        # Month name format (e.g., "march 20, 2025")
        if any(m in txt_lower for m in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]):
            if entity_text.isupper():
                return fake_date.strftime("%B %d, %Y").upper()
            elif entity_text.islower():
                return fake_date.strftime("%B %d, %Y").lower()
            else:
                return fake_date.strftime("%B %d, %Y")
        
        # ISO format ("2025-05-22")
        if "-" in entity_text:
            return fake_date.strftime("%Y-%m-%d")
        
        # Slash format ("22/05/2025")
        if "/" in entity_text:
            return fake_date.strftime("%d/%m/%Y")
            
        return fake_date.strftime("%B %d, %Y")

    def _generate_synthetic_phone(self, entity_text: str) -> str:
        digits = re.sub(r'\D', '', entity_text)
        if entity_text.startswith("+91") or entity_text.startswith("+"):
            return f"+91 {random.randint(6, 9)}{random.randint(100000000, 999999999)}"
        elif "-" in entity_text:
            return f"0{random.randint(10, 99)}-{random.randint(10000000, 99999999)}"
        else:
            return f"{random.randint(6, 9)}{random.randint(100000000, 999999999)}"

    def get_replacement(self, entity_text: str, entity_type: str) -> str:
        key = entity_text.strip().lower()
        if key in self.entity_map:
            return self.entity_map[key]

        if entity_type == "FULL_NAME":
            if entity_text.isupper():
                synthetic = self.fake.name().upper()
            elif entity_text.islower():
                synthetic = self.fake.name().lower()
            else:
                synthetic = self.fake.name()
        elif entity_type == "EMAIL":
            email_val = f"{self.fake.first_name()}.{self.fake.last_name()}@example.org"
            synthetic = email_val.upper() if entity_text.isupper() else email_val.lower()
        elif entity_type == "PHONE_NUMBER":
            synthetic = self._generate_synthetic_phone(entity_text)
        elif entity_type == "COMPANY_NAME":
            if entity_text.isupper():
                synthetic = self.fake.company().upper()
            elif entity_text.islower():
                synthetic = self.fake.company().lower()
            else:
                synthetic = self.fake.company()
        elif entity_type == "ADDRESS":
            addr_val = f"{random.randint(10, 99)}, {self.fake.street_name()}, {self.fake.city()} - {random.randint(100000, 999999)}, India"
            synthetic = addr_val.upper() if entity_text.isupper() else (addr_val.lower() if entity_text.islower() else addr_val)
        elif entity_type == "SSN_TAX_ID":
            if len(entity_text) == 10 and entity_text.isalnum():
                synthetic = f"ABCDE{random.randint(1000, 9999)}K"
            else:
                synthetic = f"9{random.randint(10, 99)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        elif entity_type == "CREDIT_CARD":
            synthetic = self.fake.credit_card_number()
        elif entity_type == "DATE_OF_BIRTH":
            synthetic = self._generate_synthetic_date(entity_text)
        elif entity_type == "IP_ADDRESS":
            synthetic = f"192.0.2.{random.randint(1, 254)}"
        elif entity_type == "CIN_DIN":
            if "DIN" in entity_text.upper():
                if entity_text.upper().startswith("DIN"):
                    synthetic = f"DIN: {random.randint(10000000, 99999999)}"
                else:
                    synthetic = f"{random.randint(10000000, 99999999)}"
            else:
                synthetic = f"U{random.randint(10000, 99999)}MH2000PLC{random.randint(100000, 999999)}"
        else:
            synthetic = f"[REDACTED_{entity_type}]"

        self.entity_map[key] = synthetic
        return synthetic
