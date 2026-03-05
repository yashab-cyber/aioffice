"""Persistent memory system for agents — read/write/search memories."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional
from core.database import get_db


class AgentMemory:
    """Each agent gets a namespaced memory store backed by SQLite."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    # ── write ──────────────────────────────────────────────
    async def remember(self, key: str, value: str, category: str = "general"):
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO agent_memory (agent_id, category, key, value, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(agent_id, category, key)
                   DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (self.agent_id, category, key, value, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()
        finally:
            await db.close()

    # ── read ───────────────────────────────────────────────
    async def recall(self, key: str, category: str = "general") -> Optional[str]:
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT value FROM agent_memory WHERE agent_id=? AND category=? AND key=?",
                (self.agent_id, category, key),
            )
            row = await cur.fetchone()
            return row["value"] if row else None
        finally:
            await db.close()

    async def recall_category(self, category: str) -> dict[str, str]:
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT key, value FROM agent_memory WHERE agent_id=? AND category=? ORDER BY updated_at DESC",
                (self.agent_id, category),
            )
            rows = await cur.fetchall()
            return {r["key"]: r["value"] for r in rows}
        finally:
            await db.close()

    async def recall_all(self) -> dict[str, dict[str, str]]:
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT category, key, value FROM agent_memory WHERE agent_id=? ORDER BY category, updated_at DESC",
                (self.agent_id,),
            )
            rows = await cur.fetchall()
            result: dict[str, dict[str, str]] = {}
            for r in rows:
                result.setdefault(r["category"], {})[r["key"]] = r["value"]
            return result
        finally:
            await db.close()

    async def forget(self, key: str, category: str = "general"):
        db = await get_db()
        try:
            await db.execute(
                "DELETE FROM agent_memory WHERE agent_id=? AND category=? AND key=?",
                (self.agent_id, category, key),
            )
            await db.commit()
        finally:
            await db.close()

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        db = await get_db()
        try:
            cur = await db.execute(
                """SELECT category, key, value FROM agent_memory
                   WHERE agent_id=? AND (key LIKE ? OR value LIKE ?)
                   ORDER BY updated_at DESC LIMIT ?""",
                (self.agent_id, f"%{query}%", f"%{query}%", limit),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await db.close()

    # ── summary for prompt injection ───────────────────────
    async def get_context_summary(self, max_items: int = 20) -> str:
        """Return a formatted string of recent memories for LLM context."""
        db = await get_db()
        try:
            cur = await db.execute(
                """SELECT category, key, value FROM agent_memory
                   WHERE agent_id=? ORDER BY updated_at DESC LIMIT ?""",
                (self.agent_id, max_items),
            )
            rows = await cur.fetchall()
            if not rows:
                return "No memories stored yet."
            lines = []
            for r in rows:
                lines.append(f"[{r['category']}] {r['key']}: {r['value']}")
            return "\n".join(lines)
        finally:
            await db.close()
