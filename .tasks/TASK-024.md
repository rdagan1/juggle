# TASK-024: Onboarding Flow

**Phase:** Phase 4
**Complexity:** Large

## Description

Implement the 6-step onboarding conversation in Gio chat.

## Pre-condition
User just authenticated, `onboarding_completed = false`.

## Steps
1. **Step 1** (email/password only): Gio asks for name → free text → store `users.name`
2. **Step 2**: Virtual email display + forwarding toggle + action buttons
3. **Step 3**: Lecture attendance style → 3 buttons → sub-questions → store `gio_memory.lecture_mode`
4. **Step 4**: Work schedule → yes/no → if yes: multi-select work days → work hours → GCal connect option
5. **Step 5**: Notification preferences → assignment reminder lead time → exam reminder lead time
6. **Step 6**: Done message + `[העלה סילבוס עכשיו]` / `[אחר כך]`

## Resume Support
Store current step in `users.onboarding_step`; resume from last incomplete step.

**On completion:** set `onboarding_completed = true`, clear `onboarding_step`.

## Deliverable
Full onboarding renders in Gio chat. All preferences stored correctly. Skip handling works.

## Dependencies
- TASK-013 (Gio API)
- TASK-003 (auth)

## Dependencies

TASK-003, TASK-013

---

*Generated from PRD v2.7 task breakdown.*
