# TASK-010: Pdf Pipeline Celery

**Phase:** Phase 2
**Complexity:** Medium

## Description

Wire together TASK-007 and TASK-009 into the complete pipeline.

## Task: `process_pdf_attachment(pdf_attachment_id: UUID)`

## Steps (exact order)
1. Fetch `pdf_attachments` row, download PDF bytes from S3
2. Compute SHA-256 hash → check `pdf_parse_cache`
   - Cache hit: use result directly, skip to step 6
3. `extract_pdf_text()` → assess readability
4. If unreadable: update `parse_status='unreadable'`, send Gio "unreadable PDF" message, stop
5. `has_extractable_events(text)` → if False: update `parse_status='no_events'`, stop
6. `parse_pdf_with_llm()` → insert events
7. Update `parse_status='parsed'`, send Gio post-parse message

**Same task used for both email attachments (TASK-004) and manual uploads (TASK-011).**

## Deliverable
`app/tasks/pdf_pipeline.py`. End-to-end test with mock Anthropic API response.

## Dependencies
- TASK-007, TASK-009, TASK-005

## Dependencies

TASK-005, TASK-007, TASK-009

---

*Generated from PRD v2.7 task breakdown.*
