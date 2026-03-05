"""Persistent memory system for agents — read/write/search memories."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from core.database import get_db
from config import settings

logger = logging.getLogger("aioffice")


class AgentMemory:
    """Each agent gets a namespaced memory store backed by SQLite."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    # ── write ──────────────────────────────────────────────
    async def remember(self, key: str, value: str, category: str = "general", importance: int = 0):
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO agent_memory (agent_id, category, key, value, importance, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(agent_id, category, key)
                   DO UPDATE SET value=excluded.value, importance=excluded.importance, updated_at=excluded.updated_at""",
                (self.agent_id, category, key, value, importance, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()

            # Auto-cleanup if enabled
            if settings.enable_memory_cleanup:
                await self._auto_cleanup(db)
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
            if row:
                # Bump access count
                await db.execute(
                    "UPDATE agent_memory SET access_count = access_count + 1 WHERE agent_id=? AND category=? AND key=?",
                    (self.agent_id, category, key),
                )
                await db.commit()
                return row["value"]
            return None
        finally:
            await db.close()

    async def recall_category(self, category: str, limit: int = 100) -> dict[str, str]:
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT key, value FROM agent_memory WHERE agent_id=? AND category=? ORDER BY importance DESC, updated_at DESC LIMIT ?",
                (self.agent_id, category, limit),
            )
            rows = await cur.fetchall()
            return {r["key"]: r["value"] for r in rows}
        finally:
            await db.close()

    async def recall_all(self) -> dict[str, dict[str, str]]:
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT category, key, value FROM agent_memory WHERE agent_id=? ORDER BY category, importance DESC, updated_at DESC",
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

    async def forget_category(self, category: str):
        """Delete all memories in a category."""
        db = await get_db()
        try:
            await db.execute(
                "DELETE FROM agent_memory WHERE agent_id=? AND category=?",
                (self.agent_id, category),
            )
            await db.commit()
        finally:
            await db.close()

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        db = await get_db()
        try:
            cur = await db.execute(
                """SELECT category, key, value, importance FROM agent_memory
                   WHERE agent_id=? AND (key LIKE ? OR value LIKE ?)
                   ORDER BY importance DESC, updated_at DESC LIMIT ?""",
                (self.agent_id, f"%{query}%", f"%{query}%", limit),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await db.close()

    # ── summary for prompt injection ───────────────────────
    async def get_context_summary(self, max_items: int = 30) -> str:
        """Return a formatted string of recent/important memories for LLM context."""
        db = await get_db()
        try:
            # Priority: high importance first, then most recently accessed
            cur = await db.execute(
                """SELECT category, key, value FROM agent_memory
                   WHERE agent_id=? ORDER BY importance DESC, access_count DESC, updated_at DESC LIMIT ?""",
                (self.agent_id, max_items),
            )
            rows = await cur.fetchall()
            if not rows:
                return "No memories stored yet."
            lines = []
            current_cat = ""
            for r in rows:
                if r["category"] != current_cat:
                    current_cat = r["category"]
                    lines.append(f"\n### {current_cat.upper()}")
                lines.append(f"  - {r['key']}: {r['value'][:200]}")
            return "\n".join(lines)
        finally:
            await db.close()

    # ── statistics ─────────────────────────────────────────
    async def get_stats(self) -> dict:
        """Return memory usage stats."""
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT COUNT(*) as total, COUNT(DISTINCT category) as categories FROM agent_memory WHERE agent_id=?",
                (self.agent_id,),
            )
            row = await cur.fetchone()
            return {
                "total_entries": row["total"] if row else 0,
                "categories": row["categories"] if row else 0,
                "agent_id": self.agent_id,
            }
        finally:
            await db.close()

    # ── auto cleanup ──────────────────────────────────────
    async def _auto_cleanup(self, db):
        """Remove old low-importance memories when limit is exceeded."""
        max_entries = settings.memory_max_entries
        cur = await db.execute(
            "SELECT COUNT(*) as cnt FROM agent_memory WHERE agent_id=?",
            (self.agent_id,),
        )
        row = await cur.fetchone()
        if row and row["cnt"] > max_entries:
            excess = row["cnt"] - max_entries
            await db.execute(
                """DELETE FROM agent_memory WHERE id IN (
                    SELECT id FROM agent_memory WHERE agent_id=?
                    ORDER BY importance ASC, access_count ASC, updated_at ASC LIMIT ?
                )""",
                (self.agent_id, excess),
            )
            await db.commit()
            logger.debug(f"[{self.agent_id}] Memory cleanup: removed {excess} old entries")
