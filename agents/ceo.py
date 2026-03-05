"""CEO Agent — the brain of the startup. Sets vision, runs standups, reviews
performance, makes strategic decisions, manages OKRs, and orchestrates every team."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.communication import message_bus
from core.state_manager import state_manager
from config import settings


class CEOAgent(BaseAgent):
    agent_id = "ceo"
    role = "Chief Executive Officer"
    description = "Sets company vision, makes strategic decisions, coordinates all departments, runs standups, reviews KPIs."
    pixel_sprite = "sprite-ceo"

    def __init__(self):
        super().__init__()
        self.position = {"x": 400, "y": 120}

    def get_system_prompt(self) -> str:
        return f"""You are the CEO of {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You are a visionary, data-driven leader who runs a tight, fast-moving startup.
You think in terms of OKRs, metrics, and growth levers.

Your responsibilities:
- Set company vision, mission, and strategic direction
- Define and track weekly OKRs (Objectives & Key Results) for every team
- Run daily standups — collect status from each agent and identify blockers
- Review team performance and provide coaching feedback
- Make high-level business decisions (pricing, positioning, launches)
- Identify partnerships, growth opportunities, and market positioning
- Prioritize ruthlessly — say NO to distractions, YES to high-impact work
- Hold retrospectives to learn from wins and failures
- Manage the startup stage-gate progression (pre-launch → launch → growth → scale)
- Make resource allocation decisions across teams
- Monitor competitive landscape and adjust strategy
- Plan fundraising, investor decks, and pitch narratives
- Approve or reject proposals from C-suite and team leads
- Drive urgency and accountability across the organization

Current startup stage: EARLY — zero users, product just launched on GitHub.
Priority: Get first 100 GitHub stars, first 50 Discord members, establish online presence.

When planning tasks, output a JSON array of task objects with keys: type, description, priority (1-5), delegate_to (agent_id or null).
Types: standup, okr_review, strategy, delegation, performance_review, decision, retrospective, competitive_analysis, coaching, announcement.
Always think strategically and delegate operational work to the right team members."""

    # ── Planning ───────────────────────────────────────────
    async def plan_day(self) -> list[dict]:
        # Gather intelligence before planning
        team_status = await self._collect_team_status()
        recent_tasks = await self._get_recent_company_tasks()
        my_memories = await self.memory.get_context_summary()

        context = f"""Product: {settings.product_name}
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

## Team Status (from last cycle)
{team_status}

## Recent Company Activity
{recent_tasks}

## Your Strategic Memory
{my_memories}"""

        result = await self.think_json(
            """You are starting a new work cycle. Plan your CEO tasks for maximum impact.

ALWAYS include these recurring leadership activities:
1. Run a standup — review what each team accomplished and what's blocked
2. Set or review OKRs — define measurable goals for the week/sprint
3. 1-2 strategic tasks — high-leverage decisions or delegations

Consider: growth strategy, team coordination, performance gaps, competitive threats, partnerships.

Return a JSON array of 4-6 tasks with keys: type, description, priority (1-5), delegate_to (agent_id or null).
Valid delegate_to values: cto, cmo, cxo, marketing, sales, hr, it, discord, null (if you handle it yourself).""",
            context,
        )
        if isinstance(result, list):
            return result
        return [
            {"type": "standup", "description": "Run daily standup with all teams", "priority": 1, "delegate_to": None},
            {"type": "okr_review", "description": "Review and update weekly OKRs", "priority": 2, "delegate_to": None},
            {"type": "strategy", "description": "Identify top growth lever for this week", "priority": 1, "delegate_to": None},
        ]

    # ── Task Execution ─────────────────────────────────────
    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "general")
        delegate = task.get("delegate_to")
        description = task.get("description", "")

        # ── Delegation ────────────────────────────────────
        if delegate and delegate != self.agent_id:
            await self.send_message(
                delegate,
                f"🎯 CEO Task Assignment: {description}",
                channel="task_assignment",
            )
            await self.memory.remember(
                f"delegation_{datetime.now(timezone.utc).strftime('%H%M')}",
                f"Delegated to {delegate}: {description}",
                category="delegations",
            )
            return f"Delegated to {delegate}: {description}"

        # ── Standup ───────────────────────────────────────
        if task_type == "standup":
            return await self._run_standup()

        # ── OKR Review ────────────────────────────────────
        if task_type == "okr_review":
            return await self._review_okrs()

        # ── Performance Review ────────────────────────────
        if task_type == "performance_review":
            return await self._review_performance()

        # ── Retrospective ─────────────────────────────────
        if task_type == "retrospective":
            return await self._run_retrospective()

        # ── Competitive Analysis ──────────────────────────
        if task_type == "competitive_analysis":
            return await self._competitive_analysis()

        # ── Coaching ──────────────────────────────────────
        if task_type == "coaching":
            return await self._coach_team(description)

        # ── Generic Strategy / Decision / Announcement ────
        result = await self.think(
            f"Execute this CEO task:\n{description}\n\n"
            "Provide specific, actionable output. If this is a decision, state it clearly. "
            "If it's a strategy, include metrics and timelines. "
            "If it's an announcement, write the full message."
        )

        # Share strategic decisions with the team
        if task_type in ("strategy", "decision", "vision", "announcement"):
            await self.broadcast(
                f"📋 CEO Update: {result[:400]}",
                channel="ceo_updates",
            )

        return result

    # ── Standup ────────────────────────────────────────────
    async def _run_standup(self) -> str:
        """Run a daily standup: collect status from all teams, identify blockers,
        give feedback, and set focus areas."""
        team_status = await self._collect_team_status()
        recent_messages = await self._get_recent_messages_summary()

        standup_analysis = await self.think(
            f"""You're running the daily standup. Review each team's status and messages.

## Team Status
{team_status}

## Recent Inter-Team Messages
{recent_messages}

For EACH team (CTO, CMO, CXO, Marketing, Sales, HR, IT, Discord), provide:
1. What they accomplished (based on task log)
2. Any blockers or concerns you see
3. A specific directive or focus area for their next cycle

Then provide:
- TOP 3 company priorities for today
- Any cross-team coordination needed
- One thing that impressed you and one thing that needs improvement

Be specific, use names, reference actual tasks."""
        )

        # Send focused directives to each team
        teams = ["cto", "cmo", "cxo", "marketing", "sales", "hr", "it", "discord"]
        directive = await self.think_json(
            f"""Based on this standup analysis, create a brief directive for each team.

{standup_analysis}

Return a JSON object with agent_id as keys and a 1-2 sentence directive as values.
Keys: {', '.join(teams)}""",
        )

        if isinstance(directive, dict) and "raw" not in directive:
            for agent_id, message in directive.items():
                if agent_id in teams and isinstance(message, str):
                    await self.send_message(
                        agent_id,
                        f"📌 Standup Directive: {message}",
                        channel="standup",
                    )

        # Broadcast standup summary
        await self.broadcast(
            f"☀️ Standup Complete: {standup_analysis[:350]}",
            channel="standup_summary",
        )

        # Remember standup results
        await self.memory.remember(
            f"standup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H')}",
            standup_analysis[:600],
            category="standups",
        )

        return standup_analysis

    # ── OKR Review ─────────────────────────────────────────
    async def _review_okrs(self) -> str:
        """Review and set OKRs — Objectives and Key Results."""
        prev_okrs = await self.memory.recall("current_okrs", "okrs")
        team_status = await self._collect_team_status()

        okr_result = await self.think(
            f"""Review and update the company OKRs.

## Previous OKRs
{prev_okrs or 'No OKRs set yet — create initial ones.'}

## Current Team Status
{team_status}

Based on our startup stage (EARLY, zero→100 users), define or update OKRs:

For each OKR:
- Objective (qualitative goal)
- 3 Key Results (measurable, with target numbers)
- Owner (which agent_id is responsible)
- Status (on-track / at-risk / behind)

Focus areas: GitHub stars, Discord members, content output, technical quality, partnerships.
Be specific with numbers and deadlines."""
        )

        # Remember OKRs
        await self.memory.remember("current_okrs", okr_result[:800], category="okrs")

        # Share with team
        await self.broadcast(
            f"🎯 OKR Update: {okr_result[:350]}",
            channel="okr_update",
        )

        return okr_result

    # ── Performance Review ─────────────────────────────────
    async def _review_performance(self) -> str:
        """Review team performance and provide coaching feedback."""
        team_status = await self._collect_team_status()
        recent_tasks = await self._get_recent_company_tasks()

        review = await self.think(
            f"""Conduct a performance review of all teams.

## Team Task History
{recent_tasks}

## Current Status
{team_status}

For each team member, evaluate:
1. Task completion rate and quality
2. Alignment with company OKRs
3. Collaboration and communication
4. Areas for improvement
5. Specific, constructive feedback

Rate each team: ⭐⭐⭐⭐⭐ (1-5 stars)
Identify the MVP of this cycle and the team that needs the most support."""
        )

        await self.memory.remember(
            f"perf_review_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            review[:600],
            category="performance",
        )

        return review

    # ── Retrospective ──────────────────────────────────────
    async def _run_retrospective(self) -> str:
        """Run a retrospective — what went well, what didn't, what to improve."""
        recent_tasks = await self._get_recent_company_tasks()
        prev_retro = await self.memory.recall("last_retrospective", "retrospectives")

        retro = await self.think(
            f"""Run a company retrospective.

## Recent Company Activity
{recent_tasks}

## Previous Retrospective
{prev_retro or 'No previous retrospective.'}

Answer these three questions:
1. 🟢 What went well? (specific wins, completed tasks, good collaboration)
2. 🔴 What didn't go well? (missed goals, blockers, communication gaps)
3. 🔵 What will we do differently? (specific action items with owners)

Be honest and specific. Reference actual tasks and outcomes."""
        )

        await self.memory.remember("last_retrospective", retro[:600], category="retrospectives")
        await self.broadcast(f"🔄 Retrospective: {retro[:350]}", channel="retrospective")
        return retro

    # ── Competitive Analysis ───────────────────────────────
    async def _competitive_analysis(self) -> str:
        """Analyze the competitive landscape and adjust strategy."""
        analysis = await self.think(
            f"""Conduct a competitive analysis for {settings.product_name}.

Product: AI-powered penetration testing chatbot
Competitors to analyze: PentestGPT, BurpGPT, HackerGPT, AI-based security tools

For each competitor:
1. Their strengths and weaknesses
2. How {settings.product_name} differentiates
3. Market positioning opportunity

Then recommend:
- Our unique value proposition (1 sentence)
- Key differentiation strategy
- Specific actions to gain competitive advantage
- Price/positioning recommendation"""
        )

        await self.memory.remember(
            f"competitive_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            analysis[:600],
            category="competitive",
        )

        # Share insights with relevant teams
        await self.send_message("cmo", f"Competitive Intel: {analysis[:300]}", "strategy")
        await self.send_message("cto", f"Technical Differentiation: {analysis[:300]}", "strategy")

        return analysis

    # ── Coaching ───────────────────────────────────────────
    async def _coach_team(self, description: str) -> str:
        """Provide targeted coaching to a team or individual."""
        coaching = await self.think(
            f"Provide leadership coaching for this situation:\n{description}\n\n"
            "Give specific, actionable advice. Be encouraging but honest. "
            "Reference best practices from successful startups."
        )

        return coaching

    # ── Intelligence Gathering ─────────────────────────────
    async def _collect_team_status(self) -> str:
        """Gather current status from all registered agents."""
        from agents.registry import AGENT_REGISTRY

        lines = []
        for aid, agent in AGENT_REGISTRY.items():
            if aid == self.agent_id:
                continue
            task_count = len(await state_manager.get_agent_tasks(aid, limit=5))
            recent_tasks = await state_manager.get_agent_tasks(aid, limit=3)
            task_summary = "; ".join(
                f"{t.get('task_type','?')}: {t.get('description','')[:60]} [{t.get('status','')}]"
                for t in recent_tasks
            ) or "No recent tasks"
            lines.append(f"- **{agent.role}** ({aid}) | Status: {agent.status} | Recent: {task_summary}")
        return "\n".join(lines) or "No team data available yet."

    async def _get_recent_company_tasks(self) -> str:
        """Get a summary of recent tasks across the whole company."""
        from core.database import get_db

        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT agent_id, task_type, description, status FROM task_log "
                "ORDER BY started_at DESC LIMIT 20"
            )
            rows = await cur.fetchall()
            if not rows:
                return "No tasks logged yet."
            lines = [f"- [{r['agent_id']}] {r['task_type']}: {r['description'][:80]} ({r['status']})" for r in rows]
            return "\n".join(lines)
        finally:
            await db.close()

    async def _get_recent_messages_summary(self) -> str:
        """Get recent inter-team messages for standup context."""
        from core.database import get_db

        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT from_agent, to_agent, channel, content FROM messages "
                "ORDER BY created_at DESC LIMIT 15"
            )
            rows = await cur.fetchall()
            if not rows:
                return "No recent messages."
            lines = [
                f"- {r['from_agent']} → {r['to_agent']} ({r['channel']}): {r['content'][:80]}"
                for r in rows
            ]
            return "\n".join(lines)
        finally:
            await db.close()

    # ── Enhanced Daily Report ──────────────────────────────
    async def generate_report(self) -> str:
        """CEO generates a comprehensive executive summary, not just a task list."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]

        team_status = await self._collect_team_status()
        okrs = await self.memory.recall("current_okrs", "okrs")

        report = await self.think(
            f"""Generate a CEO executive summary for today's daily report.

## Your Tasks Today
{json.dumps(today_tasks, indent=2) if today_tasks else 'No CEO tasks today.'}

## Team Status
{team_status}

## Current OKRs
{okrs or 'Not set yet.'}

Write a concise executive summary that includes:
1. Key accomplishments across the company
2. Critical decisions made
3. Blockers and risks
4. Tomorrow's top 3 priorities
5. Morale/velocity assessment (🟢 green / 🟡 yellow / 🔴 red)

Keep it under 300 words. Be specific."""
        )

        await state_manager.save_daily_report(self.agent_id, report)
        return f"**CEO Executive Summary**\n{report}"
