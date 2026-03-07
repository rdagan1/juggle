# TASK-015: Proactivity Scheduler

**Phase:** Phase 3
**Complexity:** Large

## Description

Implement the scheduler that sends proactive Gio messages.

## Celery Beat Schedule
Runs every 2 hours.

## Per User, Per Deadline
1. Compute `days_until` for each pending deadline
2. Look up `reminder_state` for `(user_id, deadline_id)` pair
3. Apply anti-creep rules:
   - Max 1 proactive message per topic per day
   - 3 consecutive snoozes → reduce to every 2 days (override if `days_until < 5`)
   - Skip if `silenced_until` in future
   - Skip if current time in `quiet_hours` (23:00–07:00 Jerusalem)
   - Skip if Shabbat blackout enabled and current time is Shabbat
4. If should send: call `render_gio_message()`, insert into `conversation_history`, update `reminder_state`

## Cadences
- Assignment: 10 days, 7 days (if no study block), 3 days, 1 day, day-of
- Exam: 14 days, 5 days
- Lecture (attend mode): N minutes before start
- Lecture (recording mode + prompt=true): after lecture end + delay

## Deliverable
`app/tasks/scheduler.py`. Unit test: assert correct urgency variant for each `days_until` value.

## Dependencies
- TASK-012 (personalization)
- TASK-013 (Gio API)

## Dependencies

TASK-012, TASK-013

---

*Generated from PRD v2.7 task breakdown.*
