"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
import app.models  # noqa: F401 — registers all models with Base.metadata
from app.api import auth, chat, email_webhook, upload, timeline, grades, emails, settings as settings_api, calendar, courses

settings_obj = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Juggle API",
    description="AI-powered study companion for OUI students",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings_obj.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(email_webhook.router)
app.include_router(upload.router)
app.include_router(timeline.router)
app.include_router(grades.router)
app.include_router(emails.router)
app.include_router(settings_api.router)
app.include_router(calendar.router)
app.include_router(courses.router)


# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_route(websocket: WebSocket, user_id: str):
    from app.api.chat import websocket_endpoint
    await websocket_endpoint(websocket, user_id)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "juggle-api"}
