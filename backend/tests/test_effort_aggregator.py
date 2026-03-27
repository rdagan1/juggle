"""Tests for effort aggregation."""
import pytest

from app.models.effort import EffortRecord, EffortInputMethod, EffortRecordType
from app.services.effort_aggregator import compute_aggregates


@pytest.mark.asyncio
async def test_compute_aggregates_basic(db_session):
    records = [
        EffortRecord(
            course_code="20407",
            assignment_label='ממ"ן 11',
            hours_spent=h,
            input_method=EffortInputMethod.button,
            record_type=EffortRecordType.assignment,
        )
        for h in [2.0, 3.0, 4.0, 5.0, 6.0]
    ]
    for r in records:
        db_session.add(r)
    await db_session.flush()

    await compute_aggregates(db_session)

    from sqlalchemy import select
    from app.models.effort import EffortAggregate
    result = await db_session.execute(
        select(EffortAggregate).where(EffortAggregate.course_code == "20407")
    )
    agg = result.scalar_one_or_none()
    assert agg is not None
    assert agg.sample_count == 5
    assert abs(agg.mean_hours - 4.0) < 0.01
    assert agg.p25_hours <= agg.mean_hours <= agg.p75_hours


@pytest.mark.asyncio
async def test_compute_aggregates_skips_single_record(db_session):
    db_session.add(
        EffortRecord(
            course_code="99999",
            assignment_label="יחיד",
            hours_spent=3.0,
            input_method=EffortInputMethod.typed,
            record_type=EffortRecordType.assignment,
        )
    )
    await db_session.flush()
    await compute_aggregates(db_session)

    from sqlalchemy import select
    from app.models.effort import EffortAggregate
    result = await db_session.execute(
        select(EffortAggregate).where(EffortAggregate.course_code == "99999")
    )
    agg = result.scalar_one_or_none()
    assert agg is None


@pytest.mark.asyncio
async def test_compute_aggregates_upserts(db_session):
    """Running aggregation twice should update, not duplicate."""
    for h in [1.0, 2.0, 3.0]:
        db_session.add(
            EffortRecord(
                course_code="55555",
                assignment_label="test",
                hours_spent=h,
                input_method=EffortInputMethod.button,
                record_type=EffortRecordType.assignment,
            )
        )
    await db_session.flush()

    await compute_aggregates(db_session)
    await compute_aggregates(db_session)

    from sqlalchemy import select, func
    from app.models.effort import EffortAggregate
    result = await db_session.execute(
        select(func.count()).where(EffortAggregate.course_code == "55555")
    )
    count = result.scalar()
    assert count == 1
