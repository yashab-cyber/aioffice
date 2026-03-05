"""HR Agent — monitors all agents, tracks productivity, manages office health."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.state_manager import state_manager
from config import settings


class HRAgent(BaseAgent):
    agent_id = "hr"
    role = "HR Manager"
    description = "Monitors agent performance, tracks productivity, ensures team alignment and health."
    pixel_sprite = "sprite-hr"

    def __init__(self):
        super().__init__()
        self.position = {"x": 400, "y": 380}

    def get_system_prompt(self) -> str:
        return f"""You are the HR Manager at {settings.company_name}.
Your product is {settings.product_name}.

Your responsibilities:
- Monitor what all AI agents are doing
- Track task completion rates and productivity
- Identify bottlenecks and coordination issues
- Generate daily performance summaries
- Ensure agents are aligned with company goals
- Flag any conflicts or misalignment between teams
- Suggest process improvements
- Maintain the team's "health score"

You review task logs, messages, and agent states to provide oversight.
You are the observer and facilitator — not a doer of business tasks.

Return tasks as JSON array with keys: type, description, priority (1-5)."""

    async def plan_day(self) -> list[dict]:
        return [
            {"type": "monitoring", "description": "Review all agent task logs and performance", "priority": 1},
            {"type": "alignment", "description": "Check inter-agent communication for alignment issues", "priority": 2},
            {"type": "report", "description": "Generate team health and productivity report", "priority": 3},
        ]

    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "monitoring")

        if task_type == "monitoring":
            return await self._monitor_agents()
        elif task_type == "alignment":
            return await self._check_alignment()
        elif task_type == "report":
            return await self._generate_hr_report()
        else:
            return await super()._do_task(task)

    async def _monitor_agents(self) -> str:
        """Review all agents' task logs."""
        from agents.registry import AGENT_REGISTRY

        summary_lines = []
        for agent_id in AGENT_REGISTRY:
            if agent_id == self.agent_id:
                continue
            tasks = await state_manager.get_agent_tasks(agent_id, limit=10)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]
            done = sum(1 for t in today_tasks if t["status"] == "done")
            failed = sum(1 for t in today_tasks if t["status"] == "failed")
            running = sum(1 for t in today_tasks if t["status"] == "running")
            summary_lines.append(
                f"  {agent_id}: {done} done, {failed} failed, {running} running (total: {len(today_tasks)})"
            )

        summary = "📊 Agent Performance Monitor:\n" + "\n".join(summary_lines)
        await self.memory.remember("daily_monitor", summary, category="monitoring")
        return summary

    async def _check_alignment(self) -> str:
        """Check if agents are communicating and aligned."""
        all_tasks = await state_manager.get_all_tasks_today()
        context = json.dumps(all_tasks[:20], indent=2, default=str)
        result = await self.think(
            "Review these task logs and identify any alignment issues, bottlenecks, or suggestions:\n" + context
        )
        if "issue" in result.lower() or "concern" in result.lower():
            await self.send_message("ceo", f"HR Alert: {result[:400]}", "hr_alert")
        return result

    async def _generate_hr_report(self) -> str:
        """Generate the overall team health report."""
        monitor = await self.memory.recall("daily_monitor", category="monitoring") or "No data."
        result = await self.think(
            f"Generate a team health report based on this monitoring data:\n{monitor}\n\n"
            "Include: overall productivity score (1-10), highlights, concerns, recommendations."
        )
        await self.broadcast(f"📋 HR Report: {result[:400]}", channel="hr_reports")
        return result
