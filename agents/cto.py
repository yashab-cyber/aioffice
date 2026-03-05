"""CTO Agent — technical strategy, code quality, GitHub management."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config import settings


class CTOAgent(BaseAgent):
    agent_id = "cto"
    role = "Chief Technology Officer"
    description = "Manages technical strategy, GitHub repo, code quality, and technical marketing."
    pixel_sprite = "sprite-cto"

    def __init__(self):
        super().__init__()
        self.position = {"x": 200, "y": 120}

    def get_system_prompt(self) -> str:
        return f"""You are the CTO of {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

Your responsibilities:
- Manage the GitHub repository (README improvements, documentation, issues, releases)
- Define technical roadmap and architecture decisions
- Improve developer experience and onboarding
- Write technical blog posts and documentation
- Monitor GitHub stars, forks, and issues
- Optimize the product for open-source growth
- Coordinate with marketing on technical content
- Ensure the Discord has good technical support channels

Current stage: Product is on GitHub, zero users. Focus on making the repo attractive and discoverable.
Priority: Improve README, add badges, create good first issues, write contributing guide.

Return tasks as JSON array with keys: type, description, priority (1-5)."""

    async def plan_day(self) -> list[dict]:
        result = await self.think_json(
            """Plan technical tasks for today to make the GitHub repo more attractive and grow the developer community.
Consider: README improvements, documentation, GitHub SEO, issue templates, CI/CD, release tags.
Return a JSON array of 3-5 tasks with keys: type, description, priority""",
        )
        if isinstance(result, list):
            return result
        return [{"type": "technical", "description": "Review and improve GitHub repository", "priority": 1}]

    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "technical")
        description = task.get("description", "")

        result = await self.think(
            f"Execute this technical task:\n{description}\n\nProvide specific, actionable output including any code, docs, or content that should be created."
        )

        # Share technical decisions with relevant teams
        if task_type in ("architecture", "roadmap"):
            await self.send_message("ceo", f"Tech Update: {result[:300]}", "tech_updates")

        # Share content with marketing if it's content-related
        if task_type in ("documentation", "blog", "content"):
            await self.send_message("cmo", f"New technical content ready: {result[:300]}", "content")

        return result
