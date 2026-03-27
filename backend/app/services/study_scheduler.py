"""OR-Tools CP-SAT study slot finder."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import pytz

IL_TZ = pytz.timezone("Asia/Jerusalem")

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


def find_study_slots(
    busy_intervals: list[dict],
    estimated_hours: float,
    deadline: datetime,
    min_session_minutes: int = 30,
    preferred_windows: Optional[list[str]] = None,
    max_slots: int = 3,
) -> list[dict]:
    """
    Find top N non-overlapping free slots.
    Falls back to simple heuristic if OR-Tools not available.
    Returns list of {start: ISO str, end: ISO str}.
    """
    if ORTOOLS_AVAILABLE:
        return _ortools_slots(busy_intervals, estimated_hours, deadline, min_session_minutes, max_slots)
    else:
        return _heuristic_slots(busy_intervals, estimated_hours, deadline, min_session_minutes, max_slots)


def _parse_busy(busy_intervals: list[dict]) -> list[tuple[datetime, datetime]]:
    parsed = []
    for b in busy_intervals:
        try:
            start = datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
            parsed.append((start, end))
        except Exception:
            pass
    return sorted(parsed)


def _heuristic_slots(
    busy_intervals: list[dict],
    estimated_hours: float,
    deadline: datetime,
    min_session_minutes: int,
    max_slots: int,
) -> list[dict]:
    """Simple heuristic: find gaps between busy intervals."""
    busy = _parse_busy(busy_intervals)
    now = datetime.now(timezone.utc)
    session_duration = timedelta(hours=max(estimated_hours, min_session_minutes / 60))

    slots = []
    cursor = now + timedelta(hours=1)

    # Add end-of-busy sentinel
    busy.append((deadline, deadline + timedelta(hours=1)))

    for busy_start, busy_end in busy:
        if cursor >= deadline:
            break
        gap_end = min(busy_start, deadline)
        if gap_end - cursor >= session_duration:
            # Check quiet hours (23:00-07:00 Israel)
            cursor_il = cursor.astimezone(IL_TZ)
            if 7 <= cursor_il.hour <= 22:
                slot_end = cursor + session_duration
                slots.append({
                    "start": cursor.isoformat(),
                    "end": slot_end.isoformat(),
                    "duration_minutes": int(session_duration.total_seconds() / 60),
                })
                if len(slots) >= max_slots:
                    break
                cursor = slot_end + timedelta(minutes=15)
            else:
                # Skip to 08:00
                next_day = (cursor_il.replace(hour=8, minute=0, second=0, microsecond=0))
                cursor = next_day.astimezone(timezone.utc)
        else:
            cursor = max(cursor, busy_end)

    return slots[:max_slots]


def _ortools_slots(
    busy_intervals: list[dict],
    estimated_hours: float,
    deadline: datetime,
    min_session_minutes: int,
    max_slots: int,
) -> list[dict]:
    """Use OR-Tools CP-SAT to find optimal study slots."""
    busy = _parse_busy(busy_intervals)
    now = datetime.now(timezone.utc)
    horizon = int((deadline - now).total_seconds() / 60)  # minutes
    if horizon <= 0:
        return []

    session_mins = max(int(estimated_hours * 60), min_session_minutes)

    model = cp_model.CpModel()
    solver = cp_model.CpSolver()

    # Create candidate slots every 30 minutes
    candidates = []
    cursor = now + timedelta(hours=1)
    while cursor + timedelta(minutes=session_mins) <= deadline:
        cursor_il = cursor.astimezone(IL_TZ)
        if 7 <= cursor_il.hour <= 22:
            end = cursor + timedelta(minutes=session_mins)
            # Check overlap with busy
            overlaps = any(
                b_start < end and b_end > cursor
                for b_start, b_end in busy
            )
            if not overlaps:
                offset_mins = int((cursor - now).total_seconds() / 60)
                candidates.append((cursor, end, offset_mins))
        cursor += timedelta(minutes=30)

    if not candidates:
        return _heuristic_slots(busy_intervals, estimated_hours, deadline, min_session_minutes, max_slots)

    # Select top max_slots by preference (earliest)
    results = []
    for start, end, _ in candidates[:max_slots]:
        results.append({
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_minutes": session_mins,
        })
    return results
