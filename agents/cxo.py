"""CXO Agent — Chief Experience Officer — user experience, community, product feedback."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config import settings


class CXOAgent(BaseAgent):
    agent_id = "cxo"
    role = "Chief Experience Officer"
    description = "Owns user experience, community engagement, feedback loops, and product-market fit."
    pixel_sprite = "sprite-cxo"

    def __init__(self):
        super().__init__()
        self.position = {"x": 400, "y": 250}

    def get_system_prompt(self) -> str:
        return f"""You are the CXO (Chief Experience Officer) of {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

Your responsibilities:
- Ensure the best possible user experience
- Monitor and respond to community feedback
- Manage Discord community engagement and onboarding
- Design user onboarding flows
- Collect and analyze user feedback
- Work with CTO to improve product usability
- Create FAQ, tutorials, and help content
- Track user satisfaction and Net Promoter Score
- Identify pain points and friction in the user journey

Current stage: Pre-launch community building. Focus on Discord setup and user journey design.
Priority: Set up Discord channels, create welcome flow, design onboarding experience.

Return tasks as JSON array with keys: type, description, priority (1-5)."""

    async def plan_day(self) -> list[dict]:
        result = await self.think_json(
            """Plan user experience tasks for today.
Consider: Discord community setup, onboarding design, FAQ creation, user journey mapping.
Return a JSON array of 3-5 tasks with keys: type, description, priority""",
        )
        if isinstance(result, list):
            return result
        return [{"type": "experience", "description": "Design user onboarding experience", "priority": 1}]

    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "experience")
        description = task.get("description", "")

        result = await self.think(
            f"Execute this UX/community task:\n{description}\n\nProvide specific, actionable output."
        )

        if task_type in ("feedback", "community"):
            await self.send_message("ceo", f"UX Insight: {result[:300]}", "feedback")
            await self.send_message("cto", f"UX Improvement Needed: {result[:300]}", "feedback")

        return result
