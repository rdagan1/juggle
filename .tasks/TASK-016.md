# TASK-016: Exam Date Selection

**Phase:** Phase 3
**Complexity:** Medium

## Description

Handle exam PDFs with multiple מועדים.

## Trigger
Post-parse, when `exam_sittings` has ≥2 rows for the same `deadline_id`.

## Gio Message
Render dynamic buttons, one per מועד: `[מועד א׳ — 15 באפריל, 09:00]`

## On Button Tap
- Mark selected `exam_sittings` row as `status='confirmed'`
- Mark other rows as `status='optional'`
- If Google Calendar connected: create standard GCal event for confirmed מועד, tentative events for others
- Store `gcal_event_id` on each row
- Gio confirms selection

## Change Flow
If student says "שיניתי דעתי" → Gio re-renders the מועד buttons.

## Deliverable
`app/services/exam_flow.py` + handler in TASK-013 template router.

## Dependencies
- TASK-010 (PDF pipeline)
- TASK-013 (Gio API)

## Dependencies

TASK-010, TASK-013

---

*Generated from PRD v2.7 task breakdown.*
