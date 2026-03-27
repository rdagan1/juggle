"""Tests for chat endpoints."""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_history_unauthorized(client: AsyncClient):
    response = await client.get("/api/chat/history", params={"token": "invalid"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_history_empty(client: AsyncClient, test_user, auth_token):
    response = await client.get("/api/chat/history", params={"token": auth_token})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_respond_button_ack(client: AsyncClient, test_user, auth_token):
    with patch("app.services.gio_engine.handle_response", new_callable=AsyncMock) as mock_handle:
        from app.models.conversation import ConversationHistory, ConversationRole, InputMethod
        import uuid
        from datetime import datetime, timezone

        mock_msg = ConversationHistory(
            id=uuid.uuid4(),
            user_id=test_user.id,
            role=ConversationRole.assistant,
            content="קיבלתי, תודה!",
            input_method=InputMethod.unknown,
            timestamp=datetime.now(timezone.utc),
        )
        mock_handle.return_value = mock_msg

        response = await client.post(
            "/api/chat/respond",
            json={"button_value": "ack"},
            params={"token": auth_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "assistant"
        assert data["content"] == "קיבלתי, תודה!"


@pytest.mark.asyncio
async def test_respond_typed_message(client: AsyncClient, test_user, auth_token):
    with patch("app.services.gio_engine.handle_response", new_callable=AsyncMock) as mock_handle:
        from app.models.conversation import ConversationHistory, ConversationRole, InputMethod
        import uuid
        from datetime import datetime, timezone

        mock_msg = ConversationHistory(
            id=uuid.uuid4(),
            user_id=test_user.id,
            role=ConversationRole.assistant,
            content="הבנתי!",
            input_method=InputMethod.typed,
            timestamp=datetime.now(timezone.utc),
        )
        mock_handle.return_value = mock_msg

        response = await client.post(
            "/api/chat/respond",
            json={"text": "מה הסטטוס של המטלה?"},
            params={"token": auth_token},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_history_pagination(client: AsyncClient, test_user, auth_token, db_session):
    from app.models.conversation import ConversationHistory, ConversationRole, InputMethod
    from datetime import datetime, timezone

    for i in range(5):
        msg = ConversationHistory(
            user_id=test_user.id,
            role=ConversationRole.assistant,
            content=f"הודעה {i}",
            input_method=InputMethod.unknown,
        )
        db_session.add(msg)
    await db_session.flush()

    response = await client.get(
        "/api/chat/history",
        params={"token": auth_token, "page": 1, "page_size": 3},
    )
    assert response.status_code == 200
    assert len(response.json()) == 3
