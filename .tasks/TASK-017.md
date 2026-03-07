# TASK-017: Completion Effort Flow

**Phase:** Phase 3
**Complexity:** Medium

## Description

Handle the completion check-in and crowdsourced effort data.

## Completion Handler (triggered on `completed` button tap)
1. Update `deadlines.status = 'completed'`
2. Send effort collection message with bucket buttons (5 buckets each for assignment and exam)

## Effort Submission Handler
1. Convert bucket to midpoint float (e.g. "2–4" → 3.0)
2. Insert into `effort_records` with NO `user_id`, `input_method='button_bucket'` or `'typed'`
3. Gio thanks: "תודה 🙏 עוזר לסטודנטים הבאים לתכנן."

## Nightly Aggregation: `compute_effort_aggregates()`
- Groups `effort_records` by `course_code + assignment_label`
- Requires `sample_count >= 5` before writing to `effort_aggregates`
- Computes `mean_hours`, `p25_hours`, `p75_hours`
- Stores in `effort_aggregates`, invalidates Redis cache key

## Deliverable
Flow handlers + nightly Celery task. Unit test: bucket midpoint conversion for all bucket values.

## Dependencies
- TASK-013 (Gio API)

## Dependencies

TASK-013

---

*Generated from PRD v2.7 task breakdown.*
