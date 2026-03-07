# TASK-021: Manual Record Update

**Phase:** Phase 3
**Complexity:** Medium

## Description

Handle conversational updates from students.

## NLU Trigger
Typed messages containing update intent — detected by LLM handler in TASK-013.

## Confirmation Pattern (always)
1. Student types natural language update
2. Gio rephrases and asks for confirmation with `[כן, עדכן]` `[לא, תקן]`
3. `[כן, עדכן]` → update `deadlines` row, insert `manual_update_log`, update GCal if connected
4. `[לא, תקן]` → Gio asks: "מה הפרטים הנכונים?"

## gio_memory Updates
- Store behavioral preferences mentioned in conversation
- `last_start_days_before`: updated when student marks completion

## Deliverable
`app/services/manual_update.py`. Handles date postponement, cancellation, and preference updates.

## Dependencies
- TASK-013 (Gio API)
- TASK-022 (GCal, for calendar updates)

## Dependencies

TASK-013

---

*Generated from PRD v2.7 task breakdown.*
