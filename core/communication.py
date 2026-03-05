"""Inter-agent communication bus — send, receive, broadcast messages."""

from __future__ import annotations

import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable
from core.database import get_db

logger = logging.getLogger("aioffice")


class MessageBus:
    """Central message bus for agent-to-agent communication."""

    _instance: Optional["MessageBus"] = None
    _listeners: dict[str, list[Callable]]
    _channel_subscribers: dict[str, list[str]]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners = {}
            cls._instance._channel_subscribers = {}
        return cls._instance

    # ── send ───────────────────────────────────────────────
    async def send(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        channel: str = "direct",
        metadata: dict | None = None,
        priority: int = 0,
    ) -> int:
        db = await get_db()
        try:
            cur = await db.execute(
                """INSERT INTO messages (from_agent, to_agent, channel, content, metadata, priority)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (from_agent, to_agent, channel, content, json.dumps(metadata or {}), priority),
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
        priority: int = 0,
    ):
        """Send a message to all agents except excluded ones."""
        from agents.registry import AGENT_REGISTRY

        exclude = exclude or []
        for agent_id in AGENT_REGISTRY:
            if agent_id != from_agent and agent_id not in exclude:
                await self.send(from_agent, agent_id, content, channel, priority=priority)

    async def send_to_channel(
        self,
        from_agent: str,
        channel: str,
        content: str,
        priority: int = 0,
    ):
        """Send a message to all agents subscribed to a channel."""
        subscribers = self._channel_subscribers.get(channel, [])
        for agent_id in subscribers:
            if agent_id != from_agent:
                await self.send(from_agent, agent_id, content, channel, priority=priority)

    # ── receive ────────────────────────────────────────────
    async def get_messages(
        self,
        agent_id: str,
        unread_only: bool = True,
        limit: int = 50,
        channel: str | None = None,
    ) -> list[dict]:
        db = await get_db()
        try:
            where = "to_agent=?"
            params: list = [agent_id]
            if unread_only:
                where += " AND read=0"
            if channel:
                where += " AND channel=?"
                params.append(channel)
            cur = await db.execute(
                f"SELECT * FROM messages WHERE {where} ORDER BY priority DESC, created_at DESC LIMIT ?",
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

    async def count_unread(self, agent_id: str) -> int:
        """Count unread messages for an agent."""
        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT COUNT(*) as cnt FROM messages WHERE to_agent=? AND read=0",
                (agent_id,),
            )
            row = await cur.fetchone()
            return row["cnt"] if row else 0
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

    # ── channel subscriptions ──────────────────────────────
    def subscribe_channel(self, agent_id: str, channel: str):
        """Subscribe an agent to a named channel."""
        self._channel_subscribers.setdefault(channel, [])
        if agent_id not in self._channel_subscribers[channel]:
            self._channel_subscribers[channel].append(agent_id)

    def unsubscribe_channel(self, agent_id: str, channel: str):
        if channel in self._channel_subscribers:
            self._channel_subscribers[channel] = [
                a for a in self._channel_subscribers[channel] if a != agent_id
            ]

    def get_channel_subscribers(self, channel: str) -> list[str]:
        return self._channel_subscribers.get(channel, [])

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

    # ── search ─────────────────────────────────────────────
    async def search_messages(
        self, query: str, agent_id: str | None = None, limit: int = 20
    ) -> list[dict]:
        """Search messages by content."""
        db = await get_db()
        try:
            where = "content LIKE ?"
            params: list = [f"%{query}%"]
            if agent_id:
                where += " AND (from_agent=? OR to_agent=?)"
                params.extend([agent_id, agent_id])
            cur = await db.execute(
                f"SELECT * FROM messages WHERE {where} ORDER BY created_at DESC LIMIT ?",
                (*params, limit),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await db.close()

    # ── analytics ──────────────────────────────────────────
    async def get_message_stats(self) -> dict:
        """Return message analytics."""
        db = await get_db()
        try:
            # Total messages today
            cur = await db.execute(
                "SELECT COUNT(*) as cnt FROM messages WHERE date(created_at)=date('now')"
            )
            today = (await cur.fetchone())["cnt"]

            # Messages by channel
            cur = await db.execute(
                "SELECT channel, COUNT(*) as cnt FROM messages WHERE date(created_at)=date('now') GROUP BY channel"
            )
            by_channel = {r["channel"]: r["cnt"] for r in await cur.fetchall()}

            # Most active agents
            cur = await db.execute(
                """SELECT from_agent, COUNT(*) as cnt FROM messages
                   WHERE date(created_at)=date('now') GROUP BY from_agent ORDER BY cnt DESC LIMIT 5"""
            )
            top_senders = {r["from_agent"]: r["cnt"] for r in await cur.fetchall()}

            # Unread counts per agent
            cur = await db.execute(
                "SELECT to_agent, COUNT(*) as cnt FROM messages WHERE read=0 GROUP BY to_agent"
            )
            unread = {r["to_agent"]: r["cnt"] for r in await cur.fetchall()}

            return {
                "today_total": today,
                "by_channel": by_channel,
                "top_senders": top_senders,
                "unread_by_agent": unread,
            }
        finally:
            await db.close()


# Singleton
message_bus = MessageBus()
