"""Base agent — every role inherits from this class."""

from __future__ import annotations

import json
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from config import settings
from core.memory import AgentMemory
from core.communication import message_bus
from core.state_manager import state_manager
from core.llm_provider import LLMProvider, build_provider

logger = logging.getLogger("aioffice")


class BaseAgent(ABC):
    """Abstract base class for all AI office agents."""

    agent_id: str  # e.g. "ceo", "cto"
    role: str  # e.g. "Chief Executive Officer"
    description: str  # One-liner
    pixel_sprite: str  # CSS class for the GUI sprite

    # Shared LLM provider (built once, shared across agents)
    _llm: LLMProvider | None = None
    _llm_initialized: bool = False

    @classmethod
    def init_llm(cls):
        """Initialize the shared LLM provider from settings (call once at startup)."""
        if not cls._llm_initialized:
            cls._llm = build_provider(settings)
            cls._llm_initialized = True
            if cls._llm:
                logger.info(f"LLM provider: {cls._llm.name} ({getattr(cls._llm, 'model', '?')})")
            else:
                logger.warning("No LLM provider configured — agents run in demo mode")

    def __init__(self):
        self.memory = AgentMemory(self.agent_id)
        self.__class__.init_llm()  # ensure LLM is initialized
        self._running = False
        self._current_task: str | None = None
        self._task_queue: asyncio.Queue[dict] = asyncio.Queue()
        self.status = "idle"  # idle | working | meeting | break
        self.position = {"x": 0, "y": 0}  # pixel position in GUI

    # ── abstract ───────────────────────────────────────────
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt defining this agent's role."""

    @abstractmethod
    async def plan_day(self) -> list[dict]:
        """Return a list of tasks for today based on product goals."""

    # ── AI call ────────────────────────────────────────────
    async def think(self, prompt: str, context: str = "") -> str:
        """Ask the LLM to reason and return a text response."""
        if not self._llm:
            return f"[{self.agent_id}] AI not configured — set LLM_PROVIDER and its API key"

        memory_ctx = await self.memory.get_context_summary()
        messages_ctx = await self._format_inbox()

        system = self.get_system_prompt()
        full_prompt = f"""## Your Memories
{memory_ctx}

## Unread Messages
{messages_ctx}

## Additional Context
{context}

## Current Task
{prompt}

Respond with a clear, actionable plan or output. Be specific."""

        try:
            return await self._llm.complete(system, full_prompt, temperature=0.7, max_tokens=2000)
        except Exception as e:
            logger.error(f"[{self.agent_id}] AI call failed ({self._llm.name}): {e}")
            return f"Error: {e}"

    async def think_json(self, prompt: str, context: str = "") -> dict:
        """Ask the LLM and parse a JSON response."""
        raw = await self.think(
            prompt + "\n\nRespond ONLY with valid JSON, no markdown fences.",
            context,
        )
        # strip markdown fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw, "error": "Failed to parse JSON"}

    # ── messaging helpers ──────────────────────────────────
    async def send_message(self, to_agent: str, content: str, channel: str = "direct"):
        await message_bus.send(self.agent_id, to_agent, content, channel)

    async def broadcast(self, content: str, channel: str = "announcement"):
        await message_bus.broadcast(self.agent_id, content, channel)

    async def read_messages(self) -> list[dict]:
        msgs = await message_bus.get_messages(self.agent_id)
        ids = [m["id"] for m in msgs]
        await message_bus.mark_read(ids)
        return msgs

    async def _format_inbox(self) -> str:
        msgs = await message_bus.get_messages(self.agent_id, unread_only=True, limit=10)
        if not msgs:
            return "No unread messages."
        lines = []
        for m in msgs:
            lines.append(f"From {m['from_agent']} ({m['channel']}): {m['content']}")
        return "\n".join(lines)

    # ── task execution ─────────────────────────────────────
    async def execute_task(self, task: dict) -> str:
        """Execute a single task and log it."""
        self.status = "working"
        self._current_task = task.get("description", "Unknown task")
        task_id = await state_manager.log_task(
            self.agent_id, task.get("type", "general"), self._current_task
        )
        logger.info(f"[{self.agent_id}] Starting: {self._current_task}")

        try:
            result = await self._do_task(task)
            await state_manager.complete_task(task_id, result, "done")
            # Remember what was done
            await self.memory.remember(
                f"task_{task_id}",
                json.dumps({"task": task, "result": result[:500]}),
                category="completed_tasks",
            )
            logger.info(f"[{self.agent_id}] Completed: {self._current_task}")
            return result
        except Exception as e:
            await state_manager.complete_task(task_id, str(e), "failed")
            logger.error(f"[{self.agent_id}] Failed: {self._current_task} — {e}")
            return f"Failed: {e}"
        finally:
            self.status = "idle"
            self._current_task = None

    async def _do_task(self, task: dict) -> str:
        """Override in subclasses for task-specific logic. Default uses AI."""
        result = await self.think(
            f"Execute this task and provide the output:\n{json.dumps(task, indent=2)}"
        )
        return result

    # ── daily report ───────────────────────────────────────
    async def generate_report(self) -> str:
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today_tasks = [
            t for t in tasks
            if t.get("started_at", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        ]
        if not today_tasks:
            return f"**{self.role} ({self.agent_id})**: No tasks completed today."

        task_lines = []
        for t in today_tasks:
            status_icon = "✅" if t["status"] == "done" else "❌"
            task_lines.append(f"  {status_icon} [{t['task_type']}] {t['description']}")

        report = f"**{self.role} ({self.agent_id})**\n" + "\n".join(task_lines)
        await state_manager.save_daily_report(self.agent_id, report)
        return report

    # ── state persistence ──────────────────────────────────
    async def save_state(self):
        state = {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_task": self._current_task,
            "position": self.position,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await state_manager.save_agent_state(self.agent_id, state)

    async def restore_state(self):
        state = await state_manager.load_agent_state(self.agent_id)
        if state:
            self.status = state.get("status", "idle")
            self.position = state.get("position", self.position)
            self._current_task = state.get("current_task")
            logger.info(
                f"[{self.agent_id}] Restored state — was: {self.status}, task: {self._current_task}"
            )
            # If there was an in-progress task, remember to resume
            if self._current_task:
                await self.memory.remember(
                    "resume_task",
                    self._current_task,
                    category="state",
                )

    # ── work loop ──────────────────────────────────────────
    async def work_loop(self):
        """Main working loop — plan, execute, repeat."""
        self._running = True
        await self.restore_state()

        # Check if there's a task to resume
        resume = await self.memory.recall("resume_task", category="state")
        if resume:
            logger.info(f"[{self.agent_id}] Resuming: {resume}")
            await self.memory.forget("resume_task", category="state")

        while self._running:
            try:
                # Plan tasks for the day
                tasks = await self.plan_day()
                for task in tasks:
                    if not self._running:
                        break
                    await self.execute_task(task)
                    await self.save_state()
                    await asyncio.sleep(2)  # brief pause between tasks

                # After all tasks, rest a cycle
                self.status = "idle"
                await self.save_state()
                await asyncio.sleep(30)  # Wait before next planning cycle

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.agent_id}] Work loop error: {e}")
                await asyncio.sleep(10)

        await self.save_state()

    def stop(self):
        self._running = False

    # ── serialization for API ──────────────────────────────
    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "description": self.description,
            "status": self.status,
            "current_task": self._current_task,
            "position": self.position,
            "pixel_sprite": self.pixel_sprite,
        }
