# TASK-011: Manual Pdf Upload

**Phase:** Phase 2
**Complexity:** Small

## Description

Allow students to upload PDFs directly.

## Endpoint
`POST /api/documents/upload` (multipart form, auth required)

## Logic
1. Accept PDF file, upload to S3
2. Insert `uploaded_documents` row with `parse_status='pending'`
3. Attempt course inference from filename/content (fuzzy match against user's `courses`)
4. Store `inferred_course_id` and `course_match_confidence` if confident
5. Enqueue `process_pdf_attachment(document_id)`
6. Return `202 Accepted` immediately

**If course not identified:** post-parse Gio message will ask student to identify course.

## Deliverable
Upload endpoint + drag-and-drop zone component in React frontend.

## Dependencies
- TASK-010 (PDF pipeline)
- TASK-005 (S3)

## Dependencies

TASK-005, TASK-010

---

*Generated from PRD v2.7 task breakdown.*
