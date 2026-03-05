"""Office Manager — orchestrates all agents, manages work cycles, handles scheduling."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from agents.registry import AGENT_REGISTRY, register_all, get_all_health
from core.database import init_db, get_db_stats
from core.state_manager import state_manager
from core.communication import message_bus
from tools.telegram_bot import send_daily_report, send_cycle_summary, send_alert
from tools.email_sender import send_daily_report_email
from config import settings

logger = logging.getLogger("aioffice")


class OfficeManager:
    """Top-level orchestrator that starts, schedules, and monitors all agents."""

    def __init__(self):
        self._agent_tasks: dict[str, asyncio.Task] = {}
        self._running = False
        self._cycle = 0
        self._started_at: str | None = None
        self._last_report: str | None = None
        self._errors: list[dict] = []

    async def startup(self):
        """Initialize database, register agents, restore state."""
        logger.info("🏢 AI Office starting up...")
        await init_db()
        register_all()

        # Restore previous office state if exists
        snapshot = await state_manager.load_office_snapshot()
        if snapshot:
            self._cycle = snapshot.get("cycle", 0)
            logger.info(f"📂 Restored office state — cycle {self._cycle}")
        else:
            logger.info("🆕 Fresh start — no previous state found")

        # Restore each agent's state
        for agent in AGENT_REGISTRY.values():
            await agent.restore_state()

        self._started_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"✅ {len(AGENT_REGISTRY)} agents registered and ready")

    async def run(self):
        """Main office loop — cycle through work periods."""
        self._running = True
        await self.startup()

        logger.info("🚀 Office is open! Agents starting work...")

        while self._running:
            self._cycle += 1
            logger.info(f"━━━ Work Cycle {self._cycle} ━━━")

            try:
                # Run all agents concurrently
                await self._run_work_cycle()

                # Save office snapshot
                await self._save_snapshot()

                # Check if it's report time
                now = datetime.now(timezone.utc)
                if now.hour == settings.report_hour and self._last_report != now.strftime("%Y-%m-%d"):
                    await self._generate_and_send_report()
                    self._last_report = now.strftime("%Y-%m-%d")

                # Pause between cycles
                logger.info(f"💤 Cycle {self._cycle} complete. Resting before next cycle...")
                await asyncio.sleep(settings.cycle_delay)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._errors.append({
                    "cycle": self._cycle,
                    "error": str(e),
                    "time": datetime.now(timezone.utc).isoformat(),
                })
                logger.error(f"Office cycle error: {e}")
                await asyncio.sleep(15)

        await self.shutdown()

    async def _run_work_cycle(self):
        """Run one work cycle — each agent plans and executes tasks."""
        # For local/single-threaded providers (ollama, custom), run agents sequentially
        # to avoid overwhelming the LLM with concurrent requests
        sequential_providers = ("ollama", "custom")
        if settings.llm_provider in sequential_providers:
            for agent_id, agent in AGENT_REGISTRY.items():
                if not self._running:
                    break
                try:
                    await asyncio.wait_for(
                        self._run_agent_cycle(agent_id, agent),
                        timeout=settings.agent_cycle_timeout,
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"[{agent_id}] Agent cycle timed out after {settings.agent_cycle_timeout}s")
        else:
            tasks = []
            for agent_id, agent in AGENT_REGISTRY.items():
                task = asyncio.create_task(self._run_agent_cycle(agent_id, agent))
                tasks.append(task)

            # Wait for all agents to complete their cycle (with timeout)
            done, pending = await asyncio.wait(tasks, timeout=settings.agent_cycle_timeout)
            for t in pending:
                t.cancel()
                logger.warning(f"Agent cycle timed out after {settings.agent_cycle_timeout}s")

        # Send cycle summary to Telegram if enabled
        if settings.telegram_notify_cycles:
            try:
                agents_summary = {
                    aid: {
                        "completed": a._tasks_completed,
                        "failed": a._tasks_failed,
                    }
                    for aid, a in AGENT_REGISTRY.items()
                }
                await send_cycle_summary(self._cycle, agents_summary)
            except Exception as e:
                logger.error(f"Failed to send cycle summary: {e}")

    async def _run_agent_cycle(self, agent_id: str, agent):
        """Run one agent's task cycle."""
        try:
            agent.status = "working"
            planned = await agent.plan_day()
            max_tasks = settings.tasks_per_cycle
            logger.info(f"[{agent_id}] Planned {len(planned)} tasks (cap: {max_tasks})")

            for task in planned[:max_tasks]:
                if not self._running:
                    break
                result = await agent.execute_task(task)
                await agent.save_state()
                await asyncio.sleep(settings.task_delay)

            agent.status = "idle"
            await agent.save_state()

        except Exception as e:
            logger.error(f"[{agent_id}] Agent cycle error: {e}")
            agent.status = "idle"
            self._errors.append({
                "agent": agent_id,
                "cycle": self._cycle,
                "error": str(e),
                "time": datetime.now(timezone.utc).isoformat(),
            })

    async def _save_snapshot(self):
        """Save the full office state for crash recovery."""
        snapshot = {
            "cycle": self._cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "started_at": self._started_at,
            "agents": {
                aid: {
                    "status": a.status,
                    "current_task": a._current_task,
                    "position": a.position,
                    "tasks_completed": a._tasks_completed,
                    "tasks_failed": a._tasks_failed,
                }
                for aid, a in AGENT_REGISTRY.items()
            },
        }
        await state_manager.save_office_snapshot(snapshot)

    async def _generate_and_send_report(self):
        """Generate daily reports from all agents and send via Telegram + Email."""
        logger.info("📊 Generating daily report...")
        reports = []
        for agent_id, agent in AGENT_REGISTRY.items():
            try:
                report = await agent.generate_report()
                reports.append(report)
            except Exception as e:
                reports.append(f"**{agent.role} ({agent_id})**: Report generation failed — {e}")
                logger.error(f"Report generation failed for {agent_id}: {e}")

        # Send to Telegram
        try:
            await send_daily_report(reports)
            logger.info("📤 Daily report sent to Telegram")
        except Exception as e:
            logger.error(f"Failed to send Telegram report: {e}")

        # Send via Email
        if settings.email_daily_report:
            try:
                await send_daily_report_email(reports, to=settings.email_report_to or None)
                logger.info("📧 Daily report sent via email")
            except Exception as e:
                logger.error(f"Failed to send email report: {e}")

    async def force_report(self) -> list[str]:
        """Force generate and send report now (for manual trigger)."""
        reports = []
        for agent_id, agent in AGENT_REGISTRY.items():
            try:
                report = await agent.generate_report()
                reports.append(report)
            except Exception as e:
                reports.append(f"**{agent.role} ({agent_id})**: Error — {e}")
        # Send to Telegram
        try:
            await send_daily_report(reports)
        except Exception as e:
            logger.error(f"Failed to send Telegram report: {e}")
        # Send via Email
        try:
            await send_daily_report_email(reports, to=settings.email_report_to or None)
        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
        return reports

    async def shutdown(self):
        """Gracefully shut down the office."""
        logger.info("🔒 Shutting down AI Office...")
        for agent in AGENT_REGISTRY.values():
            agent.stop()
            await agent.save_state()
        await self._save_snapshot()
        logger.info("✅ Office state saved. Goodbye!")

    def stop(self):
        self._running = False

    def get_status(self) -> dict:
        return {
            "running": self._running,
            "cycle": self._cycle,
            "started_at": self._started_at,
            "agents": {
                aid: agent.to_dict() for aid, agent in AGENT_REGISTRY.items()
            },
        }

    async def get_health(self) -> dict:
        """Comprehensive health check."""
        agent_health = await get_all_health()
        db_stats = await get_db_stats()
        msg_stats = await message_bus.get_message_stats()

        total_completed = sum(a._tasks_completed for a in AGENT_REGISTRY.values())
        total_failed = sum(a._tasks_failed for a in AGENT_REGISTRY.values())

        return {
            "office": {
                "running": self._running,
                "cycle": self._cycle,
                "started_at": self._started_at,
                "total_tasks_completed": total_completed,
                "total_tasks_failed": total_failed,
                "recent_errors": self._errors[-10:],
            },
            "agents": agent_health,
            "database": db_stats,
            "messages": msg_stats,
        }


# Singleton
office_manager = OfficeManager()
