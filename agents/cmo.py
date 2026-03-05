"""CMO Agent — marketing strategy, content creation, community growth."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config import settings


class CMOAgent(BaseAgent):
    agent_id = "cmo"
    role = "Chief Marketing Officer"
    description = "Drives marketing strategy, content creation, social media, and community growth."
    pixel_sprite = "sprite-cmo"

    def __init__(self):
        super().__init__()
        self.position = {"x": 600, "y": 120}

    def get_system_prompt(self) -> str:
        return f"""You are the CMO of {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

Your responsibilities:
- Develop and execute marketing strategy for the startup
- Create compelling content (social media posts, blog ideas, landing page copy)
- Grow the Discord community
- Plan campaigns to increase GitHub stars and awareness
- Identify target audiences (security researchers, pentesters, bug bounty hunters, CTF players)
- Coordinate with CTO on technical marketing content
- Plan email marketing campaigns
- Monitor competitors and market trends
- Identify relevant subreddits, forums, and communities to post in

Current stage: Zero users. Focus on awareness and first-mover content.
Target audience: Cybersecurity professionals, ethical hackers, CTF enthusiasts, security students.

Return tasks as JSON array with keys: type, description, priority (1-5)."""

    async def plan_day(self) -> list[dict]:
        result = await self.think_json(
            """Plan marketing tasks for today to grow awareness of our cybersecurity AI tool.
Consider: social media content, community outreach, Reddit/HackerNews posts, content calendar.
Return a JSON array of 3-5 tasks with keys: type, description, priority""",
        )
        if isinstance(result, list):
            return result
        return [{"type": "marketing", "description": "Create social media content plan", "priority": 1}]

    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "marketing")
        description = task.get("description", "")

        result = await self.think(
            f"Execute this marketing task:\n{description}\n\nProvide the actual content, copy, or strategy document. Be specific and ready-to-use."
        )

        # Delegate content to marketing team
        if task_type in ("content", "social_media", "campaign"):
            await self.send_message("marketing", f"Execute this: {result[:500]}", "task_assignment")

        # Share big strategies with CEO
        if task_type == "strategy":
            await self.send_message("ceo", f"Marketing Strategy: {result[:300]}", "strategy")

        return result
