"""Tests for proactivity scheduler."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.services.scheduler import is_quiet_hours, is_shabbat, should_send_reminder


def make_dt(hour: int, weekday: int = 0) -> datetime:
    """Create a datetime in Israel timezone with given hour and weekday (0=Mon)."""
    import pytz
    IL_TZ = pytz.timezone("Asia/Jerusalem")
    base = datetime(2025, 3, 3, tzinfo=timezone.utc)  # Monday
    d = base + timedelta(days=weekday)
    d_il = d.astimezone(IL_TZ)
    return d_il.replace(hour=hour, minute=0, second=0)


def test_is_quiet_hours_night():
    assert is_quiet_hours(make_dt(hour=0)) is True
    assert is_quiet_hours(make_dt(hour=23)) is True
    assert is_quiet_hours(make_dt(hour=3)) is True


def test_is_quiet_hours_day():
    assert is_quiet_hours(make_dt(hour=9)) is False
    assert is_quiet_hours(make_dt(hour=18)) is False
    assert is_quiet_hours(make_dt(hour=22)) is False


def test_is_shabbat_saturday():
    # Saturday = weekday 5
    assert is_shabbat(make_dt(hour=10, weekday=5)) is True


def test_is_shabbat_friday():
    # Friday = weekday 4
    assert is_shabbat(make_dt(hour=10, weekday=4)) is False


def test_should_send_reminder_first_time():
    now = datetime.now(timezone.utc)
    prefs = {"assignment_first_reminder_days": 7}
    assert should_send_reminder(None, 7, prefs, now) is True
    assert should_send_reminder(None, 3, prefs, now) is True
    assert should_send_reminder(None, 1, prefs, now) is True
    assert should_send_reminder(None, 0, prefs, now) is True


def test_should_send_reminder_not_on_other_days():
    now = datetime.now(timezone.utc)
    prefs = {"assignment_first_reminder_days": 7}
    assert should_send_reminder(None, 10, prefs, now) is False
    assert should_send_reminder(None, 5, prefs, now) is False
    assert should_send_reminder(None, 2, prefs, now) is False


def test_should_send_reminder_respects_silenced_until():
    from app.models.reminder_state import ReminderState
    import uuid

    now = datetime.now(timezone.utc)
    rs = ReminderState(
        user_id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        target_type="deadline",
        silenced_until=now + timedelta(days=5),
    )
    prefs = {}
    assert should_send_reminder(rs, 3, prefs, now) is False


def test_should_send_reminder_respects_24h_cooldown():
    from app.models.reminder_state import ReminderState
    import uuid

    now = datetime.now(timezone.utc)
    rs = ReminderState(
        user_id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        target_type="deadline",
        last_sent=now - timedelta(hours=12),
        send_count=1,
    )
    prefs = {}
    # Days_until=3 would normally trigger but cooldown applies
    assert should_send_reminder(rs, 3, prefs, now) is False


def test_should_send_reminder_heavy_snooze_throttle():
    from app.models.reminder_state import ReminderState
    import uuid

    now = datetime.now(timezone.utc)
    rs = ReminderState(
        user_id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        target_type="deadline",
        last_sent=now - timedelta(hours=30),
        snooze_count=3,
        send_count=5,
    )
    prefs = {}
    # 3+ snoozes + days_until > 5 → throttle to every 2 days
    # 30h < 48h so should NOT send
    assert should_send_reminder(rs, 7, prefs, now) is False
