"""Sales Team Agent — outreach, partnerships, lead generation."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config import settings


class SalesAgent(BaseAgent):
    agent_id = "sales"
    role = "Sales Team Lead"
    description = "Handles outreach, partnerships, lead generation, and business development."
    pixel_sprite = "sprite-sales"

    def __init__(self):
        super().__init__()
        self.position = {"x": 200, "y": 250}

    def get_system_prompt(self) -> str:
        return f"""You are the Sales Team Lead at {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

Your responsibilities:
- Identify potential partners and collaborators in the cybersecurity space
- Draft outreach emails to security companies, blogs, YouTubers, influencers
- Research potential enterprise customers
- Create partnership proposals
- Track leads and outreach pipeline
- Coordinate with marketing on lead nurturing
- Identify cybersecurity conferences and events for promotion
- Build relationships with cybersecurity communities

Current stage: Zero users, open-source freemium model.
Focus: Partner outreach, influencer collaboration, community engagement rather than direct sales.

Return tasks as JSON array with keys: type, description, priority (1-5)."""

    async def plan_day(self) -> list[dict]:
        result = await self.think_json(
            """Plan business development tasks for today.
Consider: partner identification, outreach emails, conference research, influencer outreach.
Return a JSON array of 3-5 tasks with keys: type, description, priority""",
        )
        if isinstance(result, list):
            return result
        return [{"type": "outreach", "description": "Research cybersecurity influencers for partnerships", "priority": 1}]

    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "outreach")
        description = task.get("description", "")

        result = await self.think(
            f"Execute this sales/BD task:\n{description}\n\nProvide specific, actionable output. If it's an email draft, write the full email."
        )

        # Share partnership opportunities with CEO
        if task_type in ("partnership", "enterprise"):
            await self.send_message("ceo", f"BD Opportunity: {result[:300]}", "business")

        return result
