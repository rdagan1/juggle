"""Nightly batch: compute effort aggregates from anonymous records."""
import statistics
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.effort import EffortRecord, EffortAggregate, EffortRecordType


async def compute_aggregates(db: AsyncSession):
    """Compute mean, p25, p75 per course+assignment+type. Run nightly."""
    # Fetch all records grouped by course_code + assignment_label + record_type
    result = await db.execute(select(EffortRecord))
    records = result.scalars().all()

    # Group manually
    groups: dict[tuple, list[float]] = {}
    for r in records:
        key = (r.course_code, r.assignment_label, r.record_type)
        groups.setdefault(key, []).append(r.hours_spent)

    for (course_code, assignment_label, record_type), hours_list in groups.items():
        if len(hours_list) < 2:
            continue

        sorted_hours = sorted(hours_list)
        n = len(sorted_hours)
        mean = statistics.mean(sorted_hours)
        p25 = sorted_hours[max(0, int(n * 0.25) - 1)]
        p75 = sorted_hours[min(n - 1, int(n * 0.75))]

        # Upsert aggregate
        existing_result = await db.execute(
            select(EffortAggregate).where(
                EffortAggregate.course_code == course_code,
                EffortAggregate.assignment_label == assignment_label,
                EffortAggregate.record_type == record_type,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.sample_count = n
            existing.mean_hours = mean
            existing.p25_hours = p25
            existing.p75_hours = p75
            from datetime import datetime, timezone
            existing.last_computed = datetime.now(timezone.utc)
        else:
            from datetime import datetime, timezone
            agg = EffortAggregate(
                course_code=course_code,
                assignment_label=assignment_label,
                record_type=record_type,
                sample_count=n,
                mean_hours=mean,
                p25_hours=p25,
                p75_hours=p75,
            )
            db.add(agg)

    await db.flush()
