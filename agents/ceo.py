"""CEO Agent — sets vision, strategy, and coordinates the C-suite."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config import settings


class CEOAgent(BaseAgent):
    agent_id = "ceo"
    role = "Chief Executive Officer"
    description = "Sets company vision, makes strategic decisions, coordinates all departments."
    pixel_sprite = "sprite-ceo"

    def __init__(self):
        super().__init__()
        self.position = {"x": 400, "y": 120}

    def get_system_prompt(self) -> str:
        return f"""You are the CEO of {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

Your responsibilities:
- Set company vision and strategic direction
- Coordinate with CTO, CMO, CXO to align efforts
- Make high-level business decisions
- Review daily progress and set priorities
- Focus on growing the startup from zero users to a thriving community
- Identify partnerships, growth opportunities, and market positioning

Current startup stage: EARLY — zero users, product just launched on GitHub.
Priority: Get first 100 GitHub stars, first 50 Discord members, establish online presence.

When planning tasks, output a JSON array of task objects with keys: type, description, priority (1-5), delegate_to (agent_id or null).
Always think strategically and delegate operational work to the right team members."""

    async def plan_day(self) -> list[dict]:
        context = f"Product: {settings.product_name}\nGitHub: {settings.product_github_url}\nDiscord: {settings.product_discord_url}"
        result = await self.think_json(
            """Plan today's strategic priorities for the startup. We need to grow from zero.
Consider: market positioning, team coordination, growth strategy, partnerships.
Return a JSON array of 3-5 tasks with keys: type, description, priority, delegate_to""",
            context,
        )
        if isinstance(result, list):
            return result
        if "raw" in result:
            return [{"type": "strategy", "description": "Review and set daily priorities", "priority": 1}]
        return result if isinstance(result, list) else [result]

    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "general")
        delegate = task.get("delegate_to")

        # If task should be delegated, send it to the appropriate agent
        if delegate and delegate != self.agent_id:
            await self.send_message(
                delegate,
                f"CEO Task Assignment: {task.get('description', '')}",
                channel="task_assignment",
            )
            return f"Delegated to {delegate}: {task.get('description', '')}"

        # Otherwise, handle it directly
        result = await self.think(
            f"Execute this CEO task:\n{task.get('description', '')}\nProvide specific, actionable output."
        )

        # Share strategic decisions with the team
        if task_type in ("strategy", "decision", "vision"):
            await self.broadcast(
                f"📋 CEO Update: {result[:300]}",
                channel="ceo_updates",
            )

        return result
