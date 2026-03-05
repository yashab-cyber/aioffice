"""State manager — save / restore full office state for crash recovery."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from core.database import get_db


class StateManager:
    """Persist and restore the running state of the entire office."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ── save individual key ────────────────────────────────
    async def save(self, key: str, value: Any):
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO office_state (key, value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (key, json.dumps(value), datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()
        finally:
            await db.close()

    async def load(self, key: str, default: Any = None) -> Any:
        db = await get_db()
        try:
            cur = await db.execute("SELECT value FROM office_state WHERE key=?", (key,))
            row = await cur.fetchone()
            return json.loads(row["value"]) if row else default
        finally:
            await db.close()

    # ── save full snapshot ─────────────────────────────────
    async def save_agent_state(self, agent_id: str, state: dict):
        await self.save(f"agent:{agent_id}:state", state)

    async def load_agent_state(self, agent_id: str) -> dict | None:
        return await self.load(f"agent:{agent_id}:state")

    async def save_office_snapshot(self, snapshot: dict):
        await self.save("office:snapshot", snapshot)

    async def load_office_snapshot(self) -> dict | None:
        return await self.load("office:snapshot")

    # ── task log helpers ───────────────────────────────────
    async def log_task(self, agent_id: str, task_type: str, description: str) -> int:
        db = await get_db()
        try:
            cur = await db.execute(
                "INSERT INTO task_log (agent_id, task_type, description, status) VALUES (?, ?, ?, 'running')",
                (agent_id, task_type, description),
            )
            await db.commit()
            return cur.lastrowid
        finally:
            await db.close()

    async def complete_task(self, task_id: int, result: str = "", status: str = "done"):
        db = await get_db()
        try:
            await db.execute(
                "UPDATE task_log SET status=?, result=?, completed_at=? WHERE id=?",
                (status, result, datetime.now(timezone.utc).isoformat(), task_id),
            )
            await db.commit()
        finally:
            await db.close()

    async def get_agent_tasks(self, agent_id: str, limit: int = 20) -> list[dict]:
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT * FROM task_log WHERE agent_id=? ORDER BY started_at DESC LIMIT ?",
                (agent_id, limit),
            )
            return [dict(r) for r in await cur.fetchall()]
        finally:
            await db.close()

    async def get_all_tasks_today(self) -> list[dict]:
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT * FROM task_log WHERE date(started_at)=date('now') ORDER BY started_at DESC"
            )
            return [dict(r) for r in await cur.fetchall()]
        finally:
            await db.close()

    # ── daily report ───────────────────────────────────────
    async def save_daily_report(self, agent_id: str, report: str):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO daily_reports (date, agent_id, report) VALUES (?, ?, ?)",
                (today, agent_id, report),
            )
            await db.commit()
        finally:
            await db.close()

    async def get_daily_reports(self, date: str | None = None) -> list[dict]:
        date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT * FROM daily_reports WHERE date=? ORDER BY agent_id",
                (date,),
            )
            return [dict(r) for r in await cur.fetchall()]
        finally:
            await db.close()


state_manager = StateManager()
