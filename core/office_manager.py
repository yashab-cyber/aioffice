"""Office Manager — orchestrates all agents, manages work cycles, handles scheduling."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from agents.registry import AGENT_REGISTRY, register_all
from core.database import init_db
from core.state_manager import state_manager
from tools.telegram_bot import send_daily_report
from config import settings

logger = logging.getLogger("aioffice")


class OfficeManager:
    """Top-level orchestrator that starts, schedules, and monitors all agents."""

    def __init__(self):
        self._agent_tasks: dict[str, asyncio.Task] = {}
        self._running = False
        self._cycle = 0

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
                if now.hour == settings.report_hour:
                    await self._generate_and_send_report()

                # Pause between cycles
                logger.info(f"💤 Cycle {self._cycle} complete. Resting before next cycle...")
                await asyncio.sleep(60)  # 1 minute between cycles

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Office cycle error: {e}")
                await asyncio.sleep(15)

        await self.shutdown()

    async def _run_work_cycle(self):
        """Run one work cycle — each agent plans and executes tasks."""
        tasks = []
        for agent_id, agent in AGENT_REGISTRY.items():
            task = asyncio.create_task(self._run_agent_cycle(agent_id, agent))
            tasks.append(task)

        # Wait for all agents to complete their cycle (with timeout)
        done, pending = await asyncio.wait(tasks, timeout=300)
        for t in pending:
            t.cancel()

    async def _run_agent_cycle(self, agent_id: str, agent):
        """Run one agent's task cycle."""
        try:
            agent.status = "working"
            planned = await agent.plan_day()
            logger.info(f"[{agent_id}] Planned {len(planned)} tasks")

            for task in planned[:5]:  # Cap at 5 tasks per cycle
                if not self._running:
                    break
                result = await agent.execute_task(task)
                await agent.save_state()
                await asyncio.sleep(1)  # Brief pause

            agent.status = "idle"
            await agent.save_state()

        except Exception as e:
            logger.error(f"[{agent_id}] Agent cycle error: {e}")
            agent.status = "idle"

    async def _save_snapshot(self):
        """Save the full office state for crash recovery."""
        snapshot = {
            "cycle": self._cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": {
                aid: {
                    "status": a.status,
                    "current_task": a._current_task,
                    "position": a.position,
                }
                for aid, a in AGENT_REGISTRY.items()
            },
        }
        await state_manager.save_office_snapshot(snapshot)

    async def _generate_and_send_report(self):
        """Generate daily reports from all agents and send via Telegram."""
        logger.info("📊 Generating daily report...")
        reports = []
        for agent_id, agent in AGENT_REGISTRY.items():
            report = await agent.generate_report()
            reports.append(report)

        # Send to Telegram
        await send_daily_report(reports)
        logger.info("📤 Daily report sent to Telegram")

    async def force_report(self) -> list[str]:
        """Force generate and send report now (for manual trigger)."""
        reports = []
        for agent_id, agent in AGENT_REGISTRY.items():
            report = await agent.generate_report()
            reports.append(report)
        await send_daily_report(reports)
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
            "agents": {
                aid: agent.to_dict() for aid, agent in AGENT_REGISTRY.items()
            },
        }


# Singleton
office_manager = OfficeManager()
