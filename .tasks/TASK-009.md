# TASK-009: Claude Haiku Pdf Parser

**Phase:** Phase 2
**Complexity:** Medium

## Description

Implement LLM-based event extraction from PDF text.

## Function: `parse_pdf_with_llm(text: str, user_id: UUID) -> dict`

## Prompt Requirements
- System: instruct Claude to extract structured events from Hebrew OUI PDFs
- Extract: assignments (ממ"נים), exams (בחינות) with all מועדים, lectures, grades
- Output: strict JSON with `events[]`, each with `type`, `title`, `course_code`, `due_date` (ISO), `confidence` (high/medium/low)
- For exams: `exam_dates[]` with `moed_label`, `sitting_date`, `location`

## After LLM Response
- Store result in `pdf_parse_cache`
- Insert events into `deadlines` / `exam_sittings` tables
- High confidence → `needs_review=false`; medium/low → `needs_review=true`
- Enqueue `send_gio_post_parse_message(user_id, parse_result)`

**Model:** `claude-3-5-haiku-20241022`

## Deliverable
`app/services/pdf_parser.py`. Integration test: parse a real OUI syllabus PDF, assert ≥1 deadline inserted.

## Dependencies
- TASK-007 (PDF extraction)
- TASK-001 (schema)

## Dependencies

TASK-007

---

*Generated from PRD v2.7 task breakdown.*
