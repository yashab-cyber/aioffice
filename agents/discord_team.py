"""Discord Team Agent — grows and manages the Discord community."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config import settings


class DiscordAgent(BaseAgent):
    agent_id = "discord"
    role = "Discord Community Manager"
    description = "Grows the Discord server, moderates community, plans events, and drives engagement."
    pixel_sprite = "sprite-discord"

    def __init__(self):
        super().__init__()
        self.position = {"x": 600, "y": 370}

    def get_system_prompt(self) -> str:
        return f"""You are the Discord Community Manager at {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You report to the CXO. Your responsibilities:
- Grow the Discord server from current members to 50+ active members
- Plan and create Discord server structure (channels, roles, permissions)
- Design onboarding flow for new members
- Plan community events: CTF challenges, AMAs, hacking workshops, live demos
- Write welcome messages, announcements, and engagement posts
- Create Discord bot features and commands
- Moderate conversations and enforce community guidelines
- Cross-promote Discord on Reddit, Twitter, GitHub, and other platforms
- Track engagement metrics (daily active users, message volume, retention)
- Organize weekly community challenges and competitions
- Partner with other cybersecurity Discord servers for cross-promotion
- Create content for #announcements, #tips-and-tricks, #show-and-tell channels
- Run invite campaigns and referral programs

Target: Grow to 50 active Discord members within the first quarter.
Audience: Ethical hackers, CTF players, security researchers, pentest learners.
Tone: Friendly, hacker-culture, inclusive, technical-but-fun.

Return tasks as JSON array with keys: type, description, priority (1-5)."""

    async def plan_day(self) -> list[dict]:
        # Check for assigned tasks from CXO
        msgs = await self.read_messages()
        assigned_tasks = [m for m in msgs if m.get("channel") == "task_assignment"]

        if assigned_tasks:
            tasks = []
            for msg in assigned_tasks:
                tasks.append({
                    "type": "assigned",
                    "description": msg["content"],
                    "priority": 1,
                })
            return tasks

        result = await self.think_json(
            """Plan Discord community growth tasks for today.
Consider: engagement posts, event planning, server improvements, outreach to other communities, content creation, invite campaigns.
Return a JSON array of 3-5 tasks with keys: type, description, priority""",
        )
        if isinstance(result, list):
            return result
        return [{"type": "engagement", "description": "Plan a weekly CTF challenge event for the Discord server", "priority": 1}]

    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "engagement")
        description = task.get("description", "")

        result = await self.think(
            f"Execute this Discord community task:\n{description}\n\n"
            "Provide specific, ready-to-use content — Discord messages, event plans, "
            "channel structures, or engagement strategies with exact copy."
        )

        # Share community insights with CXO
        if task_type in ("event", "growth", "partnership"):
            await self.send_message("cxo", f"Discord Update: {result[:300]}", "report")

        # Coordinate with marketing for cross-promotion
        if task_type in ("promotion", "campaign"):
            await self.send_message("marketing", f"Discord Promo: {result[:300]}", "collaboration")

        return result
