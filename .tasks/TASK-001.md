# TASK-001: Postgresql Schema

**Phase:** Phase 1
**Complexity:** Medium

## Description

Create the full PostgreSQL database schema as a single Alembic migration file (`migrations/versions/001_initial_schema.py`).

## Tables
- `users` — including `preferences` (JSONB) and `gio_memory` (JSONB)
- `courses`
- `deadlines` — status enum: `pending | completed | missed`
- `exam_sittings`
- `parsed_emails`
- `pdf_attachments`
- `uploaded_documents`
- `grades`
- `study_blocks`
- `effort_records` — no `user_id` (anonymous)
- `effort_aggregates`
- `reminder_state`
- `manual_update_log`
- `conversation_history` — `input_method` enum: `button | typed | unknown`
- `pdf_parse_cache` — fields: `id`, `pdf_hash` (unique), `parse_result` (JSONB), `parsed_at`, `hit_count` (default 0), `created_at`

## Deliverable
Single Alembic migration file at `migrations/versions/001_initial_schema.py`.

## Dependencies

None

---

*Generated from PRD v2.7 task breakdown.*
