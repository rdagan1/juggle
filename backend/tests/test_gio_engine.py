"""Tests for Gio engine routing and template handler."""
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.services.gio_engine import (
    EFFORT_BUCKETS,
    KNOWN_BUTTON_VALUES,
    SNOOZE_CONFIGS,
    template_handler,
)


@pytest.mark.asyncio
async def test_template_handler_ack(test_user, db_session):
    result = await template_handler(test_user.id, db_session, "ack", None)
    assert result.role.value == "assistant"
    assert "תודה" in result.content or "הבנתי" in result.content


@pytest.mark.asyncio
async def test_template_handler_dismiss(test_user, db_session):
    result = await template_handler(test_user.id, db_session, "dismiss", None)
    assert result.role.value == "assistant"


@pytest.mark.asyncio
async def test_template_handler_effort_bucket(test_user, db_session):
    result = await template_handler(test_user.id, db_session, "effort_bucket_2", None)
    assert result.role.value == "assistant"
    assert "1.5" in result.content or "שעות" in result.content


@pytest.mark.asyncio
async def test_template_handler_completed_no_deadline(test_user, db_session):
    result = await template_handler(test_user.id, db_session, "completed", None)
    assert result.role.value == "assistant"


@pytest.mark.asyncio
async def test_template_handler_completed_with_deadline(test_user, db_session):
    from app.models.course import Course
    from app.models.deadline import Deadline, DeadlineType, DeadlineStatus, DeadlineSource
    from app.models.conversation import ConversationHistory, ConversationRole, InputMethod
    from datetime import timedelta

    course = Course(user_id=test_user.id, name="מתמטיקה", code="20407")
    db_session.add(course)
    await db_session.flush()

    dl = Deadline(
        course_id=course.id,
        type=DeadlineType.assignment,
        title='ממ"ן 11',
        due_date=datetime.now(timezone.utc) + timedelta(days=3),
        source=DeadlineSource.email,
    )
    db_session.add(dl)
    await db_session.flush()

    # Create context message with deadline_id metadata
    ctx_msg = ConversationHistory(
        user_id=test_user.id,
        role=ConversationRole.assistant,
        content="יש לך מטלה",
        input_method=InputMethod.unknown,
        message_metadata=json.dumps({"deadline_id": str(dl.id)}),
    )
    db_session.add(ctx_msg)
    await db_session.flush()

    result = await template_handler(test_user.id, db_session, "completed", ctx_msg)
    assert result.role.value == "assistant"
    # Should trigger effort collection
    assert result.template_id == "effort_collection_assignment"
    assert result.buttons is not None


@pytest.mark.asyncio
async def test_snooze_handler_updates_reminder_state(test_user, db_session):
    from app.models.reminder_state import ReminderState
    from app.models.conversation import ConversationHistory, ConversationRole, InputMethod

    target_id = uuid.uuid4()
    rs = ReminderState(
        user_id=test_user.id,
        target_id=target_id,
        target_type="deadline",
        send_count=1,
    )
    db_session.add(rs)
    await db_session.flush()

    ctx_msg = ConversationHistory(
        user_id=test_user.id,
        role=ConversationRole.assistant,
        content="תזכורת",
        input_method=InputMethod.unknown,
        message_metadata=json.dumps({"target_id": str(target_id), "target_type": "deadline"}),
    )
    db_session.add(ctx_msg)
    await db_session.flush()

    result = await template_handler(test_user.id, db_session, "snooze_1w", ctx_msg)
    assert result.role.value == "assistant"
    assert "שבוע" in result.content

    # Check silenced_until was set
    await db_session.refresh(rs)
    assert rs.silenced_until is not None
    assert rs.snooze_count == 1


def test_known_button_values_includes_all_snooze():
    for key in SNOOZE_CONFIGS:
        assert key in KNOWN_BUTTON_VALUES


def test_known_button_values_includes_all_buckets():
    for key in EFFORT_BUCKETS:
        assert key in KNOWN_BUTTON_VALUES


@pytest.mark.asyncio
async def test_llm_handler_fallback_on_api_error(test_user, db_session):
    from app.services.gio_engine import llm_handler

    with patch("app.services.gio_engine.anthropic_client.messages.create", side_effect=Exception("API error")):
        result = await llm_handler(test_user.id, db_session, "שאלה כלשהי", None)
        assert result.role.value == "assistant"
        assert "מצטער" in result.content
