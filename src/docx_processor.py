import docx
from typing import Dict, Tuple, List
from redactor import PIIRedactor

class DocxProcessor:
    """Parses and redacts DOCX documents preserving inline formatting and table layouts."""

    def __init__(self, redactor: PIIRedactor):
        self.redactor = redactor

    def process_document(self, input_path: str, output_path: str) -> Dict:
        doc = docx.Document(input_path)
        total_paragraphs = 0
        total_tables = 0
        total_redacted = 0
        category_counts: Dict[str, int] = {}

        # 1. Process Body Paragraphs
        for paragraph in doc.paragraphs:
            total_paragraphs += 1
            count, cats = self._redact_paragraph(paragraph)
            total_redacted += count
            for c, k in cats.items():
                category_counts[c] = category_counts.get(c, 0) + k

        # 2. Process Tables
        for table in doc.tables:
            total_tables += 1
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        count, cats = self._redact_paragraph(paragraph)
                        total_redacted += count
                        for c, k in cats.items():
                            category_counts[c] = category_counts.get(c, 0) + k

        # 3. Process Headers and Footers
        for section in doc.sections:
            for header in [section.header, section.first_page_header, section.even_page_header]:
                if header and not header.is_linked_to_previous:
                    for paragraph in header.paragraphs:
                        count, cats = self._redact_paragraph(paragraph)
                        total_redacted += count
                        for c, k in cats.items():
                            category_counts[c] = category_counts.get(c, 0) + k
            for footer in [section.footer, section.first_page_footer, section.even_page_footer]:
                if footer and not footer.is_linked_to_previous:
                    for paragraph in footer.paragraphs:
                        count, cats = self._redact_paragraph(paragraph)
                        total_redacted += count
                        for c, k in cats.items():
                            category_counts[c] = category_counts.get(c, 0) + k

        doc.save(output_path)
        return {
            "total_paragraphs": total_paragraphs,
            "total_tables": total_tables,
            "total_redacted": total_redacted,
            "category_counts": category_counts,
            "mapping_count": len(self.redactor.entity_map)
        }

    def _redact_paragraph(self, paragraph) -> Tuple[int, Dict[str, int]]:
        text = paragraph.text
        if not text or not text.strip():
            return 0, {}

        spans = self.redactor.detect_entities(text)
        if not spans:
            return 0, {}

        cats: Dict[str, int] = {}
        for s in spans:
            t = s["type"]
            cats[t] = cats.get(t, 0) + 1

        self._apply_run_replacements(paragraph, spans)
        return len(spans), cats

    def _apply_run_replacements(self, paragraph, spans: List[Dict]):
        if not paragraph.runs:
            return

        sorted_spans = sorted(spans, key=lambda s: s["start"], reverse=True)
        for span in sorted_spans:
            replacement = self.redactor.get_replacement(span["text"], span["type"])
            start_offset = span["start"]
            end_offset = span["end"]

            current_pos = 0
            for run in paragraph.runs:
                run_len = len(run.text)
                run_start = current_pos
                run_end = current_pos + run_len
                current_pos = run_end

                if max(run_start, start_offset) < min(run_end, end_offset):
                    if start_offset >= run_start and end_offset <= run_end:
                        local_start = start_offset - run_start
                        local_end = end_offset - run_start
                        run.text = run.text[:local_start] + replacement + run.text[local_end:]
                    else:
                        local_start = max(0, start_offset - run_start)
                        local_end = min(run_len, end_offset - run_start)
                        if run_start <= start_offset < run_end:
                            run.text = run.text[:local_start] + replacement
                        else:
                            run.text = run.text[local_end:]
