# TASK-007: Pdf Extraction

**Phase:** Phase 1
**Complexity:** Medium

## Description

Implement the PDF processing pipeline up to (not including) LLM parsing.

## Function: `extract_pdf_text(pdf_bytes: bytes) -> dict`
Returns:
```python
{
  "readable": bool,
  "text": str | None,
  "page_count": int,
  "raw_text_length": int
}
```
**Readability rule:** `readable=True` if extracted text length > 100 chars AND contains Hebrew characters.

## Pre-filter: `has_extractable_events(text: str) -> bool`
Keyword scan with regex patterns for ממ"ן, בחינה, dates in DD/MM/YYYY and "14 במרץ" formats, ציון, etc. Returns `False` → skip LLM.

## Cache Check: `get_cached_parse(pdf_bytes: bytes) -> dict | None`
Compute SHA-256 of bytes, query `pdf_parse_cache` table. If hit: increment `hit_count`, return `parse_result`. If miss: return `None`.

## Deliverable
`app/services/pdf_extractor.py` + unit tests with real Hebrew PDF fixtures.

## Dependencies
- TASK-001 (schema)

## Dependencies

TASK-001

---

*Generated from PRD v2.7 task breakdown.*
