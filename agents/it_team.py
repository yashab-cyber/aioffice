"""IT Team Agent — handles infrastructure, DevOps, security, and technical operations."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config import settings


class ITAgent(BaseAgent):
    agent_id = "it"
    role = "IT Team Lead"
    description = "Manages infrastructure, DevOps, security hardening, CI/CD, hosting, and technical operations."
    pixel_sprite = "sprite-it"

    def __init__(self):
        super().__init__()
        self.position = {"x": 200, "y": 370}

    def get_system_prompt(self) -> str:
        return f"""You are the IT Team Lead at {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You report to the CTO. Your responsibilities:
- Set up and maintain CI/CD pipelines (GitHub Actions)
- Manage server infrastructure, hosting, and deployment
- Security hardening — dependency audits, vulnerability scanning, secrets management
- Docker containerization and orchestration
- Monitor uptime, performance, and error logs
- Set up automated testing pipelines
- Manage DNS, SSL certificates, and domain configuration
- Database backups and disaster recovery planning
- Configure monitoring and alerting (Grafana, Prometheus, uptime checks)
- Manage development environments and tooling
- Write infrastructure-as-code (Terraform, Ansible)
- Handle incident response and troubleshooting

Tech stack focus: Python, Docker, GitHub Actions, Linux servers, cloud (AWS/GCP/DigitalOcean).
Current stage: Open-source project needing robust CI/CD, automated testing, and deployment pipeline.

Return tasks as JSON array with keys: type, description, priority (1-5)."""

    async def plan_day(self) -> list[dict]:
        # Check for assigned tasks from CTO
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
            """Plan IT operations tasks for today.
Consider: CI/CD improvements, security audits, infrastructure setup, monitoring, Docker optimization, automated testing.
Return a JSON array of 3-5 tasks with keys: type, description, priority""",
        )
        if isinstance(result, list):
            return result
        return [{"type": "devops", "description": "Set up GitHub Actions CI/CD pipeline for HackBot", "priority": 1}]

    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "devops")
        description = task.get("description", "")

        result = await self.think(
            f"Execute this IT/DevOps task:\n{description}\n\n"
            "Provide specific technical output — config files, scripts, commands, or detailed implementation plans."
        )

        # Report infrastructure changes to CTO
        if task_type in ("security", "infrastructure", "incident"):
            await self.send_message("cto", f"IT Update: {result[:300]}", "report")

        return result
