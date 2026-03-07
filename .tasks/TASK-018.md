# TASK-018: Grades Tab

**Phase:** Phase 3
**Complexity:** Medium

## Description

Build the grades view.

## Backend
`GET /api/grades` — returns all grades grouped by course, with running average per course and trend indicator.

## Frontend
- Per-course breakdown: list assignments and exams with grade, max grade, date
- Running average per course
- Trend indicator per course (↑↓→)
- Tapping a grade shows source and date
- "דווח ל-Gio" button: navigates to ג'יו tab with pre-filled message
- No manual entry form

## Grade Notification Gio Messages (from TASK-010 pipeline)
- Above average: "קיבלת {grade} על {title} ב{course} 🎉..." + feedback buttons
- Below threshold (default <70): "קיבלת {grade} על {title}. מועד ב׳ עדיין פתוח." + action buttons

## Deliverable
Grades tab with real data + grade notification messages from pipeline.

## Dependencies
- TASK-008 (chat UI)
- TASK-010 (pipeline)

## Dependencies

TASK-008, TASK-010

---

*Generated from PRD v2.7 task breakdown.*
