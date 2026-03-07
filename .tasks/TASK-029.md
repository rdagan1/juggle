# TASK-029: Rtl Polish

**Phase:** Phase 4
**Complexity:** Medium

## Description

Audit and fix RTL rendering across all React components.

## Checklist
- All text is right-aligned by default
- Chat bubbles: Gio on LEFT (assistant), user on RIGHT
- Button sets flow right-to-left
- Tab navigator labels in Hebrew
- Date formatting: DD/MM/YYYY throughout (not MM/DD)
- Numbers: left-to-right within RTL context
- Tailwind: use `rtl:` variants where needed
- Test in Chrome with `dir="rtl"` forced

## Deliverable
Audit report + all RTL issues fixed.

## Dependencies
- All frontend tasks (TASK-006, 008, 014, 018, 019, 020)

## Dependencies

TASK-006, TASK-008, TASK-014, TASK-018, TASK-019, TASK-020

---

*Generated from PRD v2.7 task breakdown.*
