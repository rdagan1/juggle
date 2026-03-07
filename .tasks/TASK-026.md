# TASK-026: Parse Confirmation Flow

**Phase:** Phase 4
**Complexity:** Medium

## Description

Handle medium/low confidence parses that need student review.

## Trigger
After LLM parse, any event with `confidence != 'high'` → sets `deadlines.needs_review = true`.

## Gio Message After Parse
- Shows parsed events summary
- Adds `[נראה נכון ✓]` `[יש שגיאה]` buttons

## On `[יש שגיאה]`
- Gio asks: "מה לא נכון?" → free text
- LLM interprets correction → re-renders confirmation with corrected data
- On `[כן, עדכן]` → update `deadlines` row, insert `manual_update_log`, clear `needs_review`

## Course Identification Flow
When course not identified from PDF → render dynamic course buttons from user's `courses`.

## Deliverable
Confirmation flow wired into post-parse Gio message sequence.

## Dependencies
- TASK-009 (PDF parser)
- TASK-013 (Gio API)

## Dependencies

TASK-009, TASK-013

---

*Generated from PRD v2.7 task breakdown.*
