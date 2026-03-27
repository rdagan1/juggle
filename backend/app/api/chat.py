"""Gio chat: REST + WebSocket endpoints."""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db, AsyncSessionLocal
from app.models.conversation import ConversationHistory, ConversationRole, InputMethod
from app.models.user import User
from app.models.api_models import GioMessageOut, GioButton, ChatRespondRequest, AttachmentRef
from app.services.gio_engine import handle_response

router = APIRouter(prefix="/api/chat", tags=["chat"])
settings = get_settings()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket) if hasattr(self.active_connections[user_id], 'discard') else None
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

    async def send_to_user(self, user_id: str, message: dict):
        conns = self.active_connections.get(user_id, [])
        disconnected = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(user_id, ws)


manager = ConnectionManager()


def _parse_buttons(buttons_json: Optional[str]) -> Optional[list[GioButton]]:
    if not buttons_json:
        return None
    try:
        data = json.loads(buttons_json)
        return [GioButton(**b) for b in data]
    except Exception:
        return None


def _msg_to_out(msg: ConversationHistory) -> GioMessageOut:
    return GioMessageOut(
        id=msg.id,
        role=msg.role.value,
        content=msg.content,
        buttons=_parse_buttons(msg.buttons),
        navigate_hint=msg.navigate_hint,
        template_id=msg.template_id,
        timestamp=msg.timestamp,
    )


async def _get_current_user(token: str, db: AsyncSession) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/history", response_model=list[GioMessageOut])
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    offset = (page - 1) * page_size
    result = await db.execute(
        select(ConversationHistory)
        .where(ConversationHistory.user_id == user.id)
        .order_by(desc(ConversationHistory.timestamp))
        .offset(offset)
        .limit(page_size)
    )
    msgs = result.scalars().all()
    return [_msg_to_out(m) for m in reversed(msgs)]


@router.post("/respond", response_model=GioMessageOut)
async def respond(
    body: ChatRespondRequest,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)

    # Store student message — use human-readable label for button presses
    input_method = InputMethod.button if body.button_value else InputMethod.typed
    content = body.button_label or body.text or body.button_value or ""
    student_msg = ConversationHistory(
        user_id=user.id,
        role=ConversationRole.user,
        content=content,
        input_method=input_method,
    )
    db.add(student_msg)
    await db.flush()

    # Route through Gio engine
    gio_msg = await handle_response(
        user_id=user.id,
        db=db,
        message_id=body.message_id,
        value=body.button_value,
        text=body.text,
        input_method=input_method.value,
        attachments=body.attachments,
    )

    # Push over WebSocket
    await manager.send_to_user(str(user.id), _msg_to_out(gio_msg).model_dump(mode="json"))
    return _msg_to_out(gio_msg)


# WebSocket endpoint — separate router at app level
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket for real-time Gio messages. Auth via ?token= query param."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            token_user_id = payload.get("sub")
        except JWTError:
            await websocket.close(code=4001)
            return

    if token_user_id != user_id:
        await websocket.close(code=4003)
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection alive — messages are pushed by backend
            data = await websocket.receive_text()
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)


async def push_gio_message(user_id: str, msg: ConversationHistory):
    """Called by services to push a new Gio message to connected clients."""
    out = GioMessageOut(
        id=msg.id,
        role=msg.role.value,
        content=msg.content,
        buttons=_parse_buttons(msg.buttons),
        navigate_hint=msg.navigate_hint,
        template_id=msg.template_id,
        timestamp=msg.timestamp,
    )
    await manager.send_to_user(user_id, out.model_dump(mode="json"))
