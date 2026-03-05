"""State manager — save / restore full office state for crash recovery."""

from __future__ import annotations

import json
import time
import logging
from datetime import datetime, timezone
from typing import Any
from core.database import get_db

logger = logging.getLogger("aioffice")


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

    async def delete(self, key: str):
        db = await get_db()
        try:
            await db.execute("DELETE FROM office_state WHERE key=?", (key,))
            await db.commit()
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
            now = datetime.now(timezone.utc).isoformat()
            # Calculate duration
            cur = await db.execute("SELECT started_at FROM task_log WHERE id=?", (task_id,))
            row = await cur.fetchone()
            duration_ms = 0
            if row and row["started_at"]:
                try:
                    start = datetime.fromisoformat(row["started_at"].replace("Z", "+00:00"))
                    duration_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
                except Exception:
                    pass
            await db.execute(
                "UPDATE task_log SET status=?, result=?, completed_at=?, duration_ms=? WHERE id=?",
                (status, result, now, duration_ms, task_id),
            )
            await db.commit()
        finally:
            await db.close()

    async def get_agent_tasks(
        self, agent_id: str, limit: int = 20, status: str | None = None, task_type: str | None = None
    ) -> list[dict]:
        db = await get_db()
        try:
            where = "agent_id=?"
            params: list = [agent_id]
            if status:
                where += " AND status=?"
                params.append(status)
            if task_type:
                where += " AND task_type=?"
                params.append(task_type)
            cur = await db.execute(
                f"SELECT * FROM task_log WHERE {where} ORDER BY started_at DESC LIMIT ?",
                (*params, limit),
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

    async def get_task_analytics(self, agent_id: str | None = None) -> dict:
        """Return task analytics for an agent or all agents."""
        db = await get_db()
        try:
            where = "date(started_at)=date('now')"
            params: list = []
            if agent_id:
                where += " AND agent_id=?"
                params.append(agent_id)

            # Totals
            cur = await db.execute(
                f"SELECT status, COUNT(*) as cnt FROM task_log WHERE {where} GROUP BY status",
                params,
            )
            by_status = {r["status"]: r["cnt"] for r in await cur.fetchall()}

            # By type
            cur = await db.execute(
                f"SELECT task_type, COUNT(*) as cnt FROM task_log WHERE {where} GROUP BY task_type ORDER BY cnt DESC",
                params,
            )
            by_type = {r["task_type"]: r["cnt"] for r in await cur.fetchall()}

            # Average duration
            cur = await db.execute(
                f"SELECT AVG(duration_ms) as avg_ms FROM task_log WHERE {where} AND duration_ms > 0",
                params,
            )
            row = await cur.fetchone()
            avg_duration = round(row["avg_ms"] / 1000, 1) if row and row["avg_ms"] else 0

            # By agent
            by_agent = {}
            if not agent_id:
                cur = await db.execute(
                    f"SELECT agent_id, COUNT(*) as cnt FROM task_log WHERE {where} GROUP BY agent_id ORDER BY cnt DESC",
                    params,
                )
                by_agent = {r["agent_id"]: r["cnt"] for r in await cur.fetchall()}

            return {
                "by_status": by_status,
                "by_type": by_type,
                "by_agent": by_agent,
                "avg_duration_seconds": avg_duration,
                "total": sum(by_status.values()),
            }
        finally:
            await db.close()

    # ── metrics ────────────────────────────────────────────
    async def log_metric(self, agent_id: str, metric_type: str, metric_value: str):
        """Log a time-series metric."""
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO agent_metrics (agent_id, metric_type, metric_value) VALUES (?, ?, ?)",
                (agent_id, metric_type, metric_value),
            )
            await db.commit()
        finally:
            await db.close()

    async def get_metrics(self, agent_id: str, metric_type: str | None = None, limit: int = 50) -> list[dict]:
        db = await get_db()
        try:
            where = "agent_id=?"
            params: list = [agent_id]
            if metric_type:
                where += " AND metric_type=?"
                params.append(metric_type)
            cur = await db.execute(
                f"SELECT * FROM agent_metrics WHERE {where} ORDER BY created_at DESC LIMIT ?",
                (*params, limit),
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

    async def get_report_dates(self, limit: int = 30) -> list[str]:
        """Return dates that have reports."""
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT DISTINCT date FROM daily_reports ORDER BY date DESC LIMIT ?",
                (limit,),
            )
            return [r["date"] for r in await cur.fetchall()]
        finally:
            await db.close()

    # ── delegation tracking ────────────────────────────────
    async def log_delegation(self, from_agent: str, to_agent: str, description: str) -> int:
        db = await get_db()
        try:
            cur = await db.execute(
                "INSERT INTO delegations (from_agent, to_agent, task_description) VALUES (?, ?, ?)",
                (from_agent, to_agent, description),
            )
            await db.commit()
            return cur.lastrowid
        finally:
            await db.close()

    async def get_delegations(self, agent_id: str, direction: str = "to", limit: int = 20) -> list[dict]:
        db = await get_db()
        try:
            col = "to_agent" if direction == "to" else "from_agent"
            cur = await db.execute(
                f"SELECT * FROM delegations WHERE {col}=? ORDER BY created_at DESC LIMIT ?",
                (agent_id, limit),
            )
            return [dict(r) for r in await cur.fetchall()]
        finally:
            await db.close()


state_manager = StateManager()
