"""SQLite-backed database layer for persistence."""

from __future__ import annotations

import aiosqlite
import json
from pathlib import Path
from config import settings

DB_PATH = settings.resolve(settings.database_path)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    importance INTEGER DEFAULT 0,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, category, key)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'direct',
    content TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    priority INTEGER DEFAULT 0,
    read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result TEXT DEFAULT '',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS office_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    report TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    metric_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS delegations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    task_description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Core indexes
CREATE INDEX IF NOT EXISTS idx_memory_agent ON agent_memory(agent_id, category);
CREATE INDEX IF NOT EXISTS idx_memory_updated ON agent_memory(agent_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_to ON messages(to_agent, read);
CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_agent, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON task_log(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_date ON task_log(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON task_log(task_type, agent_id);
CREATE INDEX IF NOT EXISTS idx_reports_date ON daily_reports(date, agent_id);
CREATE INDEX IF NOT EXISTS idx_metrics_agent ON agent_metrics(agent_id, metric_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_delegations_to ON delegations(to_agent, status);
"""

# Migrations for upgrading existing databases
_MIGRATIONS = [
    # Add columns that may not exist in older schemas
    "ALTER TABLE agent_memory ADD COLUMN importance INTEGER DEFAULT 0",
    "ALTER TABLE agent_memory ADD COLUMN access_count INTEGER DEFAULT 0",
    "ALTER TABLE messages ADD COLUMN priority INTEGER DEFAULT 0",
    "ALTER TABLE task_log ADD COLUMN duration_ms INTEGER DEFAULT 0",
]


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    await db.execute("PRAGMA busy_timeout=5000")
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript(_SCHEMA)
        await db.commit()

        # Run migrations (ignore errors for already-applied changes)
        for migration in _MIGRATIONS:
            try:
                await db.execute(migration)
                await db.commit()
            except Exception:
                pass  # Column already exists
    finally:
        await db.close()


async def get_db_stats() -> dict:
    """Return database statistics for monitoring."""
    db = await get_db()
    try:
        stats = {}
        for table in ["agent_memory", "messages", "task_log", "daily_reports", "agent_metrics", "delegations"]:
            cur = await db.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            row = await cur.fetchone()
            stats[table] = row["cnt"] if row else 0

        # DB file size
        stats["db_size_mb"] = round(DB_PATH.stat().st_size / (1024 * 1024), 2) if DB_PATH.exists() else 0
        return stats
    finally:
        await db.close()
