# TASK-014: Timeline Tab

**Phase:** Phase 2
**Complexity:** Medium

## Description

Build the read-only timeline view.

## Backend
`GET /api/timeline?days=30` — returns all `deadlines` for authed user, sorted by `due_date`, with joined course name, type, status badge, and effort estimate.

## Frontend
- Chronological list of items within 30 days + beyond
- Each item: course name, type (ממ"ן / בחינה / הרצאה), date (DD/MM/YYYY), status badge, effort estimate (~6.5 שעות)
- Urgent strip at top for items due within 72 hours
- Tapping item opens detail card with Gio context summary and two action buttons
- RTL layout throughout

## Deliverable
Timeline tab fully populated from real data.

## Dependencies
- TASK-008 (chat UI)
- TASK-013 (Gio API)

## Dependencies

TASK-008, TASK-013

---

*Generated from PRD v2.7 task breakdown.*
