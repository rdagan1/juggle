# TASK-023: Study Slot Booking

**Phase:** Phase 4
**Complexity:** Medium

## Description

Wire together conflict detection and calendar event creation.

## Flow Trigger
User taps `[כן, אמצא זמן ללמוד]` or `[כן, קבע]`

## Steps
1. Call `get_free_slots()` for the deadline's estimated hours
2. Render dynamic slot buttons (max 3): e.g. `[רביעי 19:00–21:30]`
3. User taps a slot:
   - If GCal connected: create event titled "לימוד: {course_name}"
   - Insert `study_blocks` row with `status='scheduled'`
   - Gio confirms booking
4. 1 hour before study block: Celery Beat sends reminder Gio message

**If no GCal connected:** slots generated from `work_days`/`work_hours` + `preferred_study_windows`.

## OR-Tools Integration (optional)
`app/services/study_scheduler.py` — CP-SAT solver. Fallback: simple greedy slot finder.

## Deliverable
Full slot booking flow working end-to-end.

## Dependencies
- TASK-022 (GCal)
- TASK-015 (scheduler)

## Dependencies

TASK-015, TASK-022

---

*Generated from PRD v2.7 task breakdown.*
