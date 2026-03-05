"""FastAPI server — serves the GUI and provides API endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from config import settings
from core.office_manager import office_manager
from core.state_manager import state_manager
from core.communication import message_bus
from core.database import get_db
from core.llm_provider import list_providers, build_provider
from agents.registry import AGENT_REGISTRY
from agents.base_agent import BaseAgent

logger = logging.getLogger("aioffice")

# ── Event stream for live GUI updates ─────────────────────
_event_subscribers: list[asyncio.Queue] = []


async def _push_event(event_type: str, data: dict):
    dead = []
    for q in _event_subscribers:
        try:
            q.put_nowait({"event": event_type, "data": json.dumps(data)})
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _event_subscribers.remove(q)


# ── Lifespan ──────────────────────────────────────────────
_office_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _office_task
    # Background office loop
    _office_task = asyncio.create_task(office_manager.run())
    # Push status updates every 3 seconds
    asyncio.create_task(_status_pusher())
    yield
    office_manager.stop()
    if _office_task:
        _office_task.cancel()
        try:
            await _office_task
        except asyncio.CancelledError:
            pass


async def _status_pusher():
    """Push office status to SSE clients every few seconds."""
    while True:
        try:
            status = office_manager.get_status()
            await _push_event("status", status)
        except Exception:
            pass
        await asyncio.sleep(3)


# ── App ───────────────────────────────────────────────────
app = FastAPI(title="AI Office", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="gui/static"), name="static")
templates = Jinja2Templates(directory="gui/templates")


# ── Pages ─────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "settings": settings})


# ── SSE stream ────────────────────────────────────────────
@app.get("/api/events")
async def event_stream(request: Request):
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    _event_subscribers.append(q)

    async def gen():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15)
                    yield msg
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            if q in _event_subscribers:
                _event_subscribers.remove(q)

    return EventSourceResponse(gen())


# ── API: Office Status ────────────────────────────────────
@app.get("/api/status")
async def get_status():
    return office_manager.get_status()


# ── API: Agent Details ────────────────────────────────────
@app.get("/api/agents")
async def list_agents():
    return {aid: a.to_dict() for aid, a in AGENT_REGISTRY.items()}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = AGENT_REGISTRY.get(agent_id)
    if not agent:
        return JSONResponse({"error": "Agent not found"}, status_code=404)
    return agent.to_dict()


@app.get("/api/agents/{agent_id}/memory")
async def get_agent_memory(agent_id: str):
    agent = AGENT_REGISTRY.get(agent_id)
    if not agent:
        return JSONResponse({"error": "Agent not found"}, status_code=404)
    return await agent.memory.recall_all()


@app.get("/api/agents/{agent_id}/tasks")
async def get_agent_tasks(agent_id: str, limit: int = 20):
    return await state_manager.get_agent_tasks(agent_id, limit)


# ── API: Messages ─────────────────────────────────────────
@app.get("/api/messages")
async def get_all_messages(limit: int = 50):
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT * FROM messages ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


@app.get("/api/messages/{agent_id}")
async def get_agent_messages(agent_id: str, limit: int = 30):
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT * FROM messages WHERE from_agent=? OR to_agent=? ORDER BY created_at DESC LIMIT ?",
            (agent_id, agent_id, limit),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


# ── API: Tasks ────────────────────────────────────────────
@app.get("/api/tasks")
async def get_all_tasks(limit: int = 50):
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT * FROM task_log ORDER BY started_at DESC LIMIT ?", (limit,)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


# ── API: Daily Report ─────────────────────────────────────
@app.get("/api/reports")
async def get_reports(date: str | None = None):
    return await state_manager.get_daily_reports(date)


@app.post("/api/reports/generate")
async def force_generate_report():
    reports = await office_manager.force_report()
    return {"reports": reports}


# ── API: Director Commands ────────────────────────────────
@app.post("/api/director/message")
async def director_message(request: Request):
    """Director (user) sends a message to an agent or all agents."""
    body = await request.json()
    to = body.get("to", "ceo")
    content = body.get("message", "")
    if not content:
        return JSONResponse({"error": "Message required"}, status_code=400)

    if to == "all":
        await message_bus.broadcast("director", content, channel="director")
    else:
        await message_bus.send("director", to, content, channel="director")
    return {"status": "sent", "to": to}


@app.post("/api/office/stop")
async def stop_office():
    office_manager.stop()
    return {"status": "stopping"}


# ── API: LLM Provider Info ───────────────────────────
@app.get("/api/llm/providers")
async def get_llm_providers():
    """Return all supported LLM providers and their available models."""
    current = settings.llm_provider
    provider = BaseAgent._llm
    return {
        "current_provider": current,
        "current_model": getattr(provider, "model", None) if provider else None,
        "providers": list_providers(),
    }


@app.get("/api/llm/status")
async def get_llm_status():
    provider = BaseAgent._llm
    return {
        "active": provider is not None,
        "provider": provider.name if provider else None,
        "model": getattr(provider, "model", None) if provider else None,
    }


@app.post("/api/office/restart")
async def restart_office():
    global _office_task
    office_manager.stop()
    if _office_task:
        _office_task.cancel()
    await asyncio.sleep(1)
    _office_task = asyncio.create_task(office_manager.run())
    return {"status": "restarting"}
