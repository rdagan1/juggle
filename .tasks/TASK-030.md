# TASK-030: E2E Test Suite

**Phase:** Phase 4
**Complexity:** Medium

## Description

Write E2E tests covering the two critical happy paths.

## Test 1 — Email with readable PDF
1. POST to `/webhooks/email/inbound` with a test PDF attachment
2. Assert: PDF uploaded to S3, Celery task enqueued
3. Run task synchronously (eager mode)
4. Assert: `deadlines` row inserted, `conversation_history` row inserted
5. Assert: Gio message contains correct course name and days_until

## Test 2 — Student completes assignment
1. POST to `/api/chat/message` with `button_value='completed'`
2. Assert: `deadlines.status = 'completed'`
3. Assert: effort collection Gio message returned with 5 bucket buttons
4. POST bucket tap
5. Assert: `effort_records` row inserted with no `user_id`

## Deliverable
`tests/e2e/test_core_flows.py`. Both tests pass with a real test DB (not mocked).

## Dependencies
- All Phase 1–3 tasks

## Dependencies

None

---

*Generated from PRD v2.7 task breakdown.*
