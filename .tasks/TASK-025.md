# TASK-025: Batched Llm Reminders

**Phase:** Phase 4
**Complexity:** Medium

## Description

Implement the daily 06:00 batch job for LLM-generated nudges.

## Celery Beat Task
`generate_daily_llm_reminders()` — runs at 06:00 Asia/Jerusalem

## Logic
1. Find all users who need an LLM-generated nudge today
2. Build batch prompt: one JSON object per user with `name`, `assignment`, `course`, `days_until`, `last_start_days_before`, `other_due_count`
3. Single Claude Haiku call — return `user_id|reminder_text` per line, max 120 chars, Hebrew, warm tone
4. Parse response, call `schedule_gio_message(user_id, text, buttons=get_reminder_buttons(user_id))` for each
5. Log batch size and total tokens used

**Routing rule:** nudges requiring LLM go to this batch; urgent reminders with `days_until < 1` go real-time.

## Deliverable
`app/tasks/batch_reminders.py`. Unit test: mock 5-user batch, assert 5 messages scheduled.

## Dependencies
- TASK-015 (scheduler)
- TASK-017 (effort flow, for `last_start_days_before`)

## Dependencies

TASK-015, TASK-017

---

*Generated from PRD v2.7 task breakdown.*
