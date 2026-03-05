"""Base agent — every role inherits from this class."""

from __future__ import annotations

import json
import asyncio
import logging
import time
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

    # Rate limiter state (shared across all agents)
    _last_llm_call: float = 0.0
    _llm_lock: asyncio.Lock | None = None

    @classmethod
    def init_llm(cls):
        """Initialize the shared LLM provider from settings (call once at startup)."""
        if not cls._llm_initialized:
            cls._llm = build_provider(settings)
            cls._llm_lock = asyncio.Lock()
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
        # Performance tracking
        self._tasks_completed = 0
        self._tasks_failed = 0
        self._total_llm_calls = 0
        self._cycle_count = 0
        self._last_active: str | None = None
        self._started_at: str = datetime.now(timezone.utc).isoformat()

    # ── abstract ───────────────────────────────────────────
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt defining this agent's role."""

    @abstractmethod
    async def plan_day(self) -> list[dict]:
        """Return a list of tasks for today based on product goals."""

    # ── rate limiting ──────────────────────────────────────
    async def _rate_limit(self):
        """Enforce minimum delay between LLM calls to avoid rate limits."""
        min_delay = settings.llm_rate_limit_delay
        if min_delay <= 0:
            return
        if self._llm_lock:
            async with self._llm_lock:
                elapsed = time.monotonic() - self.__class__._last_llm_call
                if elapsed < min_delay:
                    await asyncio.sleep(min_delay - elapsed)
                self.__class__._last_llm_call = time.monotonic()

    # ── AI call ────────────────────────────────────────────
    async def think(
        self,
        prompt: str,
        context: str = "",
        max_tokens: int | None = None,
        temperature: float = 0.7,
        include_memory: bool = True,
        include_inbox: bool = True,
    ) -> str:
        """Ask the LLM to reason and return a text response."""
        if not self._llm:
            return f"[{self.agent_id}] AI not configured — set LLM_PROVIDER and its API key"

        # Build context sections
        sections = []
        if include_memory:
            memory_ctx = await self.memory.get_context_summary(max_items=settings.memory_context_items)
            sections.append(f"## Your Memories\n{memory_ctx}")

        if include_inbox:
            messages_ctx = await self._format_inbox()
            sections.append(f"## Unread Messages\n{messages_ctx}")

        if context:
            sections.append(f"## Additional Context\n{context}")

        sections.append(f"## Current Task\n{prompt}\n\nRespond with a clear, actionable plan or output. Be specific.")

        system = self.get_system_prompt()
        full_prompt = "\n\n".join(sections)
        tok = max_tokens or settings.max_tokens_per_call

        # Retry logic with exponential backoff
        last_err = None
        for attempt in range(settings.llm_max_retries):
            try:
                await self._rate_limit()
                self._total_llm_calls += 1
                return await self._llm.complete(system, full_prompt, temperature=temperature, max_tokens=tok)
            except Exception as e:
                last_err = e
                wait = min(2 ** attempt, 30)
                logger.warning(f"[{self.agent_id}] LLM attempt {attempt + 1} failed: {e} — retrying in {wait}s")
                await asyncio.sleep(wait)

        logger.error(f"[{self.agent_id}] AI call failed after {settings.llm_max_retries} retries: {last_err}")
        return f"Error: {last_err}"

    async def think_json(self, prompt: str, context: str = "", max_tokens: int | None = None) -> dict:
        """Ask the LLM and parse a JSON response."""
        raw = await self.think(
            prompt + "\n\nRespond ONLY with valid JSON, no markdown fences.",
            context,
            max_tokens=max_tokens,
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
        msgs = await message_bus.get_messages(self.agent_id, unread_only=True, limit=15)
        if not msgs:
            return "No unread messages."
        lines = []
        for m in msgs:
            lines.append(f"From {m['from_agent']} ({m['channel']}): {m['content']}")
        return "\n".join(lines)

    # ── delegation helpers ─────────────────────────────────
    async def delegate_task(self, to_agent: str, task_description: str, context: str = ""):
        """Delegate a task to another agent via message."""
        payload = json.dumps({
            "type": "delegated_task",
            "from": self.agent_id,
            "description": task_description,
            "context": context,
            "delegated_at": datetime.now(timezone.utc).isoformat(),
        })
        await message_bus.send(self.agent_id, to_agent, payload, channel="delegation")
        await self.memory.remember(
            f"delegated_{int(time.time())}",
            f"Delegated to {to_agent}: {task_description[:200]}",
            category="delegations",
        )
        logger.info(f"[{self.agent_id}] Delegated task to {to_agent}: {task_description[:80]}")

    async def request_input(self, from_agent: str, question: str) -> None:
        """Ask another agent for input/advice."""
        await message_bus.send(self.agent_id, from_agent, f"[INPUT REQUEST] {question}", channel="consultation")

    async def get_agent_status(self, agent_id: str) -> dict | None:
        """Get another agent's current status."""
        from agents.registry import AGENT_REGISTRY
        agent = AGENT_REGISTRY.get(agent_id)
        if agent:
            return agent.to_dict()
        return None

    async def get_team_status(self) -> list[dict]:
        """Get all agents' current status."""
        from agents.registry import AGENT_REGISTRY
        return [a.to_dict() for a in AGENT_REGISTRY.values()]

    # ── intelligence helpers ───────────────────────────────
    async def _get_inbox_summary(self) -> str:
        """Get a rich summary of the inbox for planning."""
        msgs = await message_bus.get_messages(self.agent_id, unread_only=True, limit=20)
        if not msgs:
            return "No unread messages."
        by_channel: dict[str, list] = {}
        for m in msgs:
            by_channel.setdefault(m["channel"], []).append(m)
        lines = []
        for ch, ch_msgs in by_channel.items():
            lines.append(f"\n### {ch.upper()} ({len(ch_msgs)} messages)")
            for m in ch_msgs[:5]:
                lines.append(f"  - From {m['from_agent']}: {m['content'][:120]}")
        return "\n".join(lines)

    async def _get_recent_tasks_summary(self, limit: int = 10) -> str:
        """Get a summary of recent tasks for context."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=limit)
        if not tasks:
            return "No previous tasks."
        lines = []
        for t in tasks:
            icon = "✅" if t["status"] == "done" else "❌" if t["status"] == "failed" else "🔄"
            lines.append(f"  {icon} [{t['task_type']}] {t['description'][:80]}")
        return "\n".join(lines)

    async def _get_cross_agent_context(self) -> str:
        """Get relevant context from other agents' recent activity."""
        all_tasks = await state_manager.get_all_tasks_today()
        if not all_tasks:
            return "No cross-agent activity today."
        by_agent: dict[str, list] = {}
        for t in all_tasks:
            if t["agent_id"] != self.agent_id:
                by_agent.setdefault(t["agent_id"], []).append(t)
        lines = []
        for aid, tasks in by_agent.items():
            done = sum(1 for t in tasks if t["status"] == "done")
            lines.append(f"  {aid}: {done}/{len(tasks)} tasks done")
        return "\n".join(lines) if lines else "No other agent activity today."

    # ── task execution ─────────────────────────────────────
    async def execute_task(self, task: dict) -> str:
        """Execute a single task and log it."""
        self.status = "working"
        self._current_task = task.get("description", "Unknown task")
        self._last_active = datetime.now(timezone.utc).isoformat()
        task_id = await state_manager.log_task(
            self.agent_id, task.get("type", "general"), self._current_task
        )
        logger.info(f"[{self.agent_id}] Starting: {self._current_task}")

        try:
            result = await asyncio.wait_for(
                self._do_task(task),
                timeout=settings.task_timeout,
            )
            await state_manager.complete_task(task_id, result, "done")
            self._tasks_completed += 1
            # Remember what was done
            await self.memory.remember(
                f"task_{task_id}",
                json.dumps({"task": task, "result": result[:500]}),
                category="completed_tasks",
            )
            # Track performance metrics
            await state_manager.log_metric(
                self.agent_id, "task_completed", task.get("type", "general")
            )
            logger.info(f"[{self.agent_id}] Completed: {self._current_task}")
            return result
        except asyncio.TimeoutError:
            await state_manager.complete_task(task_id, "Task timed out", "timeout")
            self._tasks_failed += 1
            logger.error(f"[{self.agent_id}] Timeout: {self._current_task}")
            return "Failed: Task timed out"
        except Exception as e:
            await state_manager.complete_task(task_id, str(e), "failed")
            self._tasks_failed += 1
            await state_manager.log_metric(
                self.agent_id, "task_failed", task.get("type", "general")
            )
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
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=50)
        today_tasks = [
            t for t in tasks
            if t.get("started_at", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        ]
        if not today_tasks:
            return f"**{self.role} ({self.agent_id})**: No tasks completed today."

        done = [t for t in today_tasks if t["status"] == "done"]
        failed = [t for t in today_tasks if t["status"] in ("failed", "timeout")]

        task_lines = []
        for t in today_tasks:
            icon = "✅" if t["status"] == "done" else "⏰" if t["status"] == "timeout" else "❌"
            task_lines.append(f"  {icon} [{t['task_type']}] {t['description']}")

        header = f"**{self.role} ({self.agent_id})** — {len(done)} done, {len(failed)} failed"
        report = header + "\n" + "\n".join(task_lines)
        await state_manager.save_daily_report(self.agent_id, report)
        return report

    # ── state persistence ──────────────────────────────────
    async def save_state(self):
        state = {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_task": self._current_task,
            "position": self.position,
            "tasks_completed": self._tasks_completed,
            "tasks_failed": self._tasks_failed,
            "total_llm_calls": self._total_llm_calls,
            "cycle_count": self._cycle_count,
            "last_active": self._last_active,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await state_manager.save_agent_state(self.agent_id, state)

    async def restore_state(self):
        state = await state_manager.load_agent_state(self.agent_id)
        if state:
            self.status = state.get("status", "idle")
            self.position = state.get("position", self.position)
            self._current_task = state.get("current_task")
            self._tasks_completed = state.get("tasks_completed", 0)
            self._tasks_failed = state.get("tasks_failed", 0)
            self._total_llm_calls = state.get("total_llm_calls", 0)
            self._cycle_count = state.get("cycle_count", 0)
            self._last_active = state.get("last_active")
            logger.info(
                f"[{self.agent_id}] Restored state — was: {self.status}, "
                f"completed: {self._tasks_completed}, failed: {self._tasks_failed}"
            )
            # If there was an in-progress task, remember to resume
            if self._current_task:
                await self.memory.remember(
                    "resume_task",
                    self._current_task,
                    category="state",
                )

    # ── health check ───────────────────────────────────────
    async def health_check(self) -> dict:
        """Return agent health/readiness info."""
        mem_count = 0
        try:
            all_mem = await self.memory.recall_all()
            mem_count = sum(len(v) for v in all_mem.values())
        except Exception:
            pass
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "healthy": True,
            "llm_available": self._llm is not None,
            "tasks_completed": self._tasks_completed,
            "tasks_failed": self._tasks_failed,
            "total_llm_calls": self._total_llm_calls,
            "memory_entries": mem_count,
            "cycle_count": self._cycle_count,
            "last_active": self._last_active,
            "uptime_since": self._started_at,
        }

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
                self._cycle_count += 1
                # Plan tasks for the day
                tasks = await self.plan_day()
                for task in tasks:
                    if not self._running:
                        break
                    await self.execute_task(task)
                    await self.save_state()
                    await asyncio.sleep(settings.task_delay)

                # After all tasks, rest a cycle
                self.status = "idle"
                await self.save_state()
                await asyncio.sleep(settings.cycle_delay)

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
            "tasks_completed": self._tasks_completed,
            "tasks_failed": self._tasks_failed,
            "total_llm_calls": self._total_llm_calls,
            "cycle_count": self._cycle_count,
            "last_active": self._last_active,
        }
