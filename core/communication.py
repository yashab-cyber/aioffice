"""Inter-agent communication bus — send, receive, broadcast messages."""

from __future__ import annotations

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable
from core.database import get_db


class MessageBus:
    """Central message bus for agent-to-agent communication."""

    _instance: Optional["MessageBus"] = None
    _listeners: dict[str, list[Callable]]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners = {}
        return cls._instance

    # ── send ───────────────────────────────────────────────
    async def send(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        channel: str = "direct",
        metadata: dict | None = None,
    ) -> int:
        db = await get_db()
        try:
            cur = await db.execute(
                """INSERT INTO messages (from_agent, to_agent, channel, content, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (from_agent, to_agent, channel, content, json.dumps(metadata or {})),
            )
            await db.commit()
            msg_id = cur.lastrowid

            # notify live listeners
            if to_agent in self._listeners:
                for cb in self._listeners[to_agent]:
                    asyncio.create_task(cb(from_agent, content, channel))

            return msg_id
        finally:
            await db.close()

    async def broadcast(
        self,
        from_agent: str,
        content: str,
        channel: str = "broadcast",
        exclude: list[str] | None = None,
    ):
        """Send a message to all agents except excluded ones."""
        from agents.registry import AGENT_REGISTRY

        exclude = exclude or []
        for agent_id in AGENT_REGISTRY:
            if agent_id != from_agent and agent_id not in exclude:
                await self.send(from_agent, agent_id, content, channel)

    # ── receive ────────────────────────────────────────────
    async def get_messages(
        self,
        agent_id: str,
        unread_only: bool = True,
        limit: int = 50,
    ) -> list[dict]:
        db = await get_db()
        try:
            where = "to_agent=?"
            params: list = [agent_id]
            if unread_only:
                where += " AND read=0"
            cur = await db.execute(
                f"SELECT * FROM messages WHERE {where} ORDER BY created_at DESC LIMIT ?",
                (*params, limit),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await db.close()

    async def mark_read(self, message_ids: list[int]):
        if not message_ids:
            return
        db = await get_db()
        try:
            placeholders = ",".join("?" for _ in message_ids)
            await db.execute(
                f"UPDATE messages SET read=1 WHERE id IN ({placeholders})",
                message_ids,
            )
            await db.commit()
        finally:
            await db.close()

    # ── live listeners ─────────────────────────────────────
    def subscribe(self, agent_id: str, callback: Callable[..., Awaitable]):
        self._listeners.setdefault(agent_id, []).append(callback)

    def unsubscribe(self, agent_id: str, callback: Callable[..., Awaitable]):
        if agent_id in self._listeners:
            self._listeners[agent_id] = [
                cb for cb in self._listeners[agent_id] if cb is not callback
            ]

    # ── conversation history (for LLM context) ────────────
    async def get_conversation(
        self, agent_a: str, agent_b: str, limit: int = 20
    ) -> list[dict]:
        db = await get_db()
        try:
            cur = await db.execute(
                """SELECT * FROM messages
                   WHERE (from_agent=? AND to_agent=?) OR (from_agent=? AND to_agent=?)
                   ORDER BY created_at DESC LIMIT ?""",
                (agent_a, agent_b, agent_b, agent_a, limit),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in reversed(rows)]
        finally:
            await db.close()


# Singleton
message_bus = MessageBus()
