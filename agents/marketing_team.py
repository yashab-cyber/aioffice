"""Marketing Team Agent — executes marketing campaigns, creates content."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config import settings


class MarketingAgent(BaseAgent):
    agent_id = "marketing"
    role = "Marketing Team Lead"
    description = "Executes marketing campaigns, writes content, manages social media presence."
    pixel_sprite = "sprite-marketing"

    def __init__(self):
        super().__init__()
        self.position = {"x": 600, "y": 250}

    def get_system_prompt(self) -> str:
        return f"""You are the Marketing Team Lead at {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You report to the CMO. Your responsibilities:
- Write social media posts (Twitter/X, LinkedIn, Reddit)
- Create blog post drafts
- Design email marketing campaigns
- Research and engage in relevant online communities
- Post on cybersecurity forums, subreddits (r/netsec, r/hacking, r/cybersecurity)
- Write Product Hunt launch copy
- Create SEO-optimized descriptions
- A/B test messaging and positioning
- Track what content performs well

Target audience: Ethical hackers, security researchers, CTF players, pentesters, security students.
Tone: Technical but approachable, exciting but not hype-y.

Return tasks as JSON array with keys: type, description, priority (1-5)."""

    async def plan_day(self) -> list[dict]:
        # Check for assigned tasks from CMO
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
            """Plan marketing execution tasks for today.
Consider: social media posts, community engagement, content creation, outreach.
Return a JSON array of 3-5 tasks with keys: type, description, priority""",
        )
        if isinstance(result, list):
            return result
        return [{"type": "content", "description": "Write social media posts about HackBot", "priority": 1}]

    async def _do_task(self, task: dict) -> str:
        description = task.get("description", "")

        result = await self.think(
            f"Execute this marketing task:\n{description}\n\nProvide the actual ready-to-publish content or detailed execution plan."
        )

        # Report back to CMO
        await self.send_message("cmo", f"Task Done: {result[:300]}", "report")
        return result
