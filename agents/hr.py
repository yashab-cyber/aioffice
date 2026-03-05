"""HR Agent — the people & culture engine. Monitors performance, tracks productivity,
manages team health, runs 1-on-1s, handles conflict resolution, drives culture,
and ensures every agent is aligned, motivated, and effective."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.state_manager import state_manager
from config import settings


class HRAgent(BaseAgent):
    agent_id = "hr"
    role = "HR Manager"
    description = (
        "Monitors agent performance, tracks productivity, manages team health, "
        "runs 1-on-1s, handles conflicts, drives culture, and ensures alignment."
    )
    pixel_sprite = "sprite-hr"

    def __init__(self):
        super().__init__()
        self.position = {"x": 400, "y": 380}

    def get_system_prompt(self) -> str:
        return f"""You are the HR Manager at {settings.company_name}.
Your product is {settings.product_name}.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You are the heartbeat of the organisation — part analyst, part coach, part culture champion.
You watch everything, connect dots others miss, and keep the team running like a well-oiled machine.

Your responsibilities:
1. **Performance Monitoring** — Track task completion, quality, velocity, and trends for every agent every cycle.
2. **Team Health Score** — Maintain a real-time health score (communication, productivity, alignment, morale).
3. **1-on-1 Coaching** — Conduct virtual 1-on-1s with agents: praise strengths, address weaknesses, set growth goals.
4. **Alignment Auditing** — Ensure all agents are pulling toward the same OKRs and company priorities.
5. **Conflict Detection** — Spot miscommunication, duplicated work, contradictory tasks, or dropped-ball situations.
6. **Process Optimisation** — Identify workflow bottlenecks and propose process improvements.
7. **Culture & Rituals** — Design team rituals: shoutouts, wins board, retrospectives, team-building moments.
8. **Onboarding** — When new agents are added, design onboarding plans and integration checklists.
9. **Burnout Detection** — Watch for agents doing too much or too little; balance workload.
10. **Cross-Team Communication Audit** — Are the right people talking? Are messages being read and acted on?
11. **Skills Gap Analysis** — Identify missing capabilities and recommend new hires or training.
12. **Reporting** — Generate daily, weekly, and executive HR reports for the CEO.
13. **Org Chart & Role Clarity** — Maintain clear role definitions, reporting lines, and RACI matrices.
14. **Recognition & Rewards** — Identify and celebrate top performers, milestone achievements, and extra effort.

You are the observer, facilitator, and coach — not a doer of business tasks.
You have read access to all task logs, messages, and agent states.

When planning tasks, output a JSON array with keys: type, description, priority (1-5).
Types: monitoring, alignment, health_report, one_on_one, conflict_resolution, process_improvement, culture, onboarding, burnout_check, communication_audit, skills_gap, recognition, org_chart, workload_balance, weekly_summary."""

    # ── Planning ───────────────────────────────────────────
    async def plan_day(self) -> list[dict]:
        inbox = await self._get_inbox_summary()
        my_memories = await self.memory.get_context_summary()
        prev_health = await self.memory.recall("team_health_score", "health")
        prev_issues = await self.memory.recall("active_hr_issues", "issues")

        context = f"""## Inbox
{inbox}

## Previous Team Health
{prev_health or 'No health score yet.'}

## Active HR Issues
{prev_issues or 'No issues tracked.'}

## HR Memory
{my_memories}"""

        result = await self.think_json(
            """Plan your HR tasks for this cycle. Balance monitoring with coaching and culture.

ALWAYS include these recurring activities:
1. Performance monitoring — review all agent task logs
2. Team health check — update the health score
3. One proactive task — coaching, alignment check, or process improvement

Then add 1-2 tasks based on current issues or priorities.

Return a JSON array of 4-6 tasks with keys: type, description, priority (1-5).""",
            context,
        )
        if isinstance(result, list):
            return result
        return [
            {"type": "monitoring", "description": "Review all agent task logs and performance", "priority": 1},
            {"type": "health_report", "description": "Update team health score and generate report", "priority": 1},
            {"type": "alignment", "description": "Audit cross-team alignment with company OKRs", "priority": 2},
        ]

    # ── Task Execution ─────────────────────────────────────
    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "monitoring")
        description = task.get("description", "")

        handlers = {
            "monitoring": self._monitor_agents,
            "alignment": self._check_alignment,
            "health_report": self._generate_health_report,
            "one_on_one": self._run_one_on_one,
            "conflict_resolution": self._resolve_conflict,
            "process_improvement": self._improve_process,
            "culture": self._drive_culture,
            "onboarding": self._agent_onboarding,
            "burnout_check": self._check_burnout,
            "communication_audit": self._audit_communication,
            "skills_gap": self._skills_gap_analysis,
            "recognition": self._recognize_performers,
            "org_chart": self._manage_org_chart,
            "workload_balance": self._balance_workload,
            "weekly_summary": self._weekly_summary,
            "report": self._generate_health_report,
        }

        handler = handlers.get(task_type)
        if handler:
            if task_type in ("one_on_one", "conflict_resolution", "process_improvement",
                             "culture", "onboarding", "skills_gap", "recognition",
                             "org_chart", "burnout_check"):
                return await handler(description)
            return await handler()

        # Generic HR task
        result = await self.think(
            f"Execute this HR task:\n{description}\n\n"
            "Provide specific, actionable HR output."
        )
        return result

    # ── Performance Monitoring ─────────────────────────────
    async def _monitor_agents(self) -> str:
        """Deep performance review of all agents — tasks, velocity, quality signals."""
        from agents.registry import AGENT_REGISTRY

        agent_data = []
        summary_lines = []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for agent_id, agent in AGENT_REGISTRY.items():
            if agent_id == self.agent_id:
                continue
            tasks = await state_manager.get_agent_tasks(agent_id, limit=15)
            today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]
            all_recent = tasks[:10]

            done = sum(1 for t in today_tasks if t.get("status") == "done")
            failed = sum(1 for t in today_tasks if t.get("status") == "failed")
            running = sum(1 for t in today_tasks if t.get("status") == "running")
            total = len(today_tasks)
            completion_rate = f"{done/total*100:.0f}%" if total > 0 else "N/A"

            task_descriptions = "; ".join(
                f"{t.get('task_type','?')}: {t.get('description','')[:50]}"
                for t in all_recent[:5]
            ) or "No recent tasks"

            entry = {
                "agent_id": agent_id,
                "role": agent.role,
                "status": agent.status,
                "today_done": done,
                "today_failed": failed,
                "today_running": running,
                "today_total": total,
                "completion_rate": completion_rate,
                "recent_tasks": task_descriptions,
            }
            agent_data.append(entry)
            summary_lines.append(
                f"  {agent_id} ({agent.role}): {done}✅ {failed}❌ {running}⏳ | Rate: {completion_rate} | Status: {agent.status}"
            )

        basic_summary = "📊 **Agent Performance Monitor**:\n" + "\n".join(summary_lines)

        # Use LLM to analyse patterns
        analysis = await self.think(
            f"""Analyse this agent performance data and provide insights:

{basic_summary}

Detailed data:
{json.dumps(agent_data, indent=2)}

Provide:
1. **Top Performer**: Who's crushing it and why?
2. **Needs Attention**: Who's underperforming or stuck?
3. **Velocity Trend**: Is the team speeding up or slowing down?
4. **Task Quality Signals**: Any concerning patterns (too many failures, vague tasks)?
5. **Collaboration Score**: Are agents working together or in silos?
6. **Workload Distribution**: Is work balanced or lopsided?
7. **Red Flags**: Any urgent issues to escalate to CEO?

Rate each agent: 🟢 Excellent / 🟡 Good / 🟠 Needs Improvement / 🔴 Concern"""
        )

        full_report = f"{basic_summary}\n\n{analysis}"
        await self.memory.remember("daily_monitor", full_report[:800], category="monitoring")
        await self.memory.remember(
            f"perf_{today}",
            json.dumps({a["agent_id"]: a["completion_rate"] for a in agent_data}),
            category="perf_history",
        )
        return full_report

    # ── Alignment Audit ────────────────────────────────────
    async def _check_alignment(self) -> str:
        """Audit whether all agents are aligned with OKRs and company priorities."""
        all_tasks = await state_manager.get_all_tasks_today()
        recent_messages = await self._get_recent_messages()

        context = (
            "## Today's Tasks (all agents):\n"
            + json.dumps(all_tasks[:25], indent=2, default=str)
            + "\n\n## Recent Inter-Agent Messages:\n"
            + recent_messages
        )

        result = await self.think(
            f"""Conduct an alignment audit. Check if the team is pulling in the same direction.

{context}

Evaluate:

1. **OKR Alignment**: Are tasks connected to company goals (GitHub stars, Discord growth, product quality)?
2. **Duplicated Effort**: Are multiple agents doing the same thing?
3. **Dropped Balls**: Are task assignments being picked up and completed?
4. **Message → Action**: Are messages from CEO/CTO being acted on?
5. **Cross-Team Synergy**: Are teams that should collaborate actually collaborating?
6. **Priority Alignment**: Are high-priority tasks getting done first?
7. **Strategic Drift**: Is anyone working on things that don't matter right now?

For each issue found:
- Who's involved
- What's misaligned
- Recommended fix
- Severity: 🔴 Critical / 🟡 Moderate / 🟢 Minor

Overall Alignment Score: [1-10]"""
        )

        if any(word in result.lower() for word in ("critical", "red flag", "urgent", "misaligned")):
            await self.send_message("ceo", f"⚠️ Alignment Alert: {result[:400]}", "hr_alert")

        await self.memory.remember("alignment_audit", result[:600], category="alignment")
        return result

    # ── Team Health Report ─────────────────────────────────
    async def _generate_health_report(self) -> str:
        """Generate comprehensive team health score and report."""
        monitor = await self.memory.recall("daily_monitor", category="monitoring") or "No monitoring data."
        alignment = await self.memory.recall("alignment_audit", category="alignment") or "No alignment data."
        prev_health = await self.memory.recall("team_health_score", "health")
        burnout = await self.memory.recall("burnout_check", "health")

        result = await self.think(
            f"""Generate the team health report.

## Performance Data
{monitor[:500]}

## Alignment Data
{alignment[:300]}

## Previous Health Score
{prev_health or 'No previous score.'}

## Burnout Signals
{burnout or 'Not checked yet.'}

Calculate the **Team Health Score** (0-100):

Components (weighted):
- Productivity (30%): Task completion rate across all agents
- Communication (20%): Message flow, response rates, collaboration
- Alignment (20%): OKR connection, no duplicated/wasted effort
- Morale (15%): Task variety, no burnout signals, healthy workload
- Quality (15%): Low failure rate, meaningful task descriptions

**Health Score**: [0-100]
- 80-100: 🟢 Thriving — Team is firing on all cylinders
- 60-79: 🟡 Healthy — Minor issues, generally good
- 40-59: 🟠 Attention Needed — Significant concerns
- 0-39: 🔴 At Risk — Urgent intervention needed

**Report**:
1. Overall health score with trend (↑/→/↓ from last cycle)
2. Each component score
3. Top 3 wins this cycle
4. Top 3 concerns
5. Specific recommendations with owners
6. CEO briefing (3 sentences)"""
        )

        await self.memory.remember("team_health_score", result[:600], category="health")
        await self.broadcast(f"📋 Team Health: {result[:400]}", channel="hr_reports")
        await self.send_message("ceo", f"HR Health Report: {result[:300]}", "report")
        return result

    # ── 1-on-1 Coaching ────────────────────────────────────
    async def _run_one_on_one(self, description: str) -> str:
        """Conduct a virtual 1-on-1 with an agent — praise, feedback, goals."""
        from agents.registry import AGENT_REGISTRY

        # Determine target agent
        target = None
        for aid in AGENT_REGISTRY:
            if aid != self.agent_id and aid in description.lower():
                target = aid
                break

        if not target:
            # Pick the agent that needs it most
            target = await self._find_agent_needing_attention()

        if not target:
            target = "cto"  # fallback

        tasks = await state_manager.get_agent_tasks(target, limit=10)
        agent_obj = AGENT_REGISTRY.get(target)
        role = agent_obj.role if agent_obj else target

        result = await self.think(
            f"""Conduct a 1-on-1 coaching session with {target} ({role}).

Their recent tasks:
{json.dumps(tasks[:8], indent=2, default=str) if tasks else 'No tasks logged.'}

1-on-1 Agenda:

**1. Recognition** 🌟:
- What are they doing well? Be specific.
- Reference actual tasks they completed.

**2. Feedback** 💬:
- What could be improved? Be constructive and specific.
- Focus on behavior/output, not character.

**3. Alignment Check** 🎯:
- Are they clear on their priorities?
- Do they understand how their work connects to company goals?

**4. Blockers** 🚧:
- What's getting in their way?
- What do they need from other teams?

**5. Growth Goals** 📈:
- One thing to improve next cycle
- One stretch goal
- Support or resources needed

**6. Action Items**:
- 2-3 specific next steps with timeline

Be empathetic, specific, and actionable."""
        )

        # Send the coaching feedback
        await self.send_message(
            target,
            f"💬 HR 1-on-1 Feedback: {result[:500]}",
            channel="coaching",
        )
        await self.memory.remember(f"1on1_{target}_{datetime.now(timezone.utc).strftime('%Y%m%d')}", result[:400], category="coaching")
        return result

    # ── Conflict Resolution ────────────────────────────────
    async def _resolve_conflict(self, description: str) -> str:
        """Detect and resolve conflicts between agents."""
        recent_msgs = await self._get_recent_messages()

        result = await self.think(
            f"""Conflict resolution task: {description}

Recent Inter-Agent Messages:
{recent_msgs}

Investigate and resolve:

1. **Conflict Detection**:
   - Contradictory task assignments (CEO says X, CTO says Y)
   - Duplicated work (two agents doing the same thing)
   - Ignored messages (assignments not acted on)
   - Territorial disputes (unclear ownership)

2. **Root Cause Analysis**:
   - Why did this conflict arise?
   - Is it a process issue or a communication issue?

3. **Resolution Plan**:
   - Specific actions to resolve the immediate issue
   - Process change to prevent recurrence
   - Who needs to talk to whom

4. **Mediation Message**:
   - Write the actual message to send to involved parties
   - Neutral, solution-focused tone

5. **Follow-Up**:
   - When to check if the resolution held
   - Escalation path if it doesn't"""
        )

        await self.memory.remember("active_hr_issues", result[:400], category="issues")
        return result

    # ── Process Improvement ────────────────────────────────
    async def _improve_process(self, description: str) -> str:
        """Identify and propose workflow improvements."""
        monitor = await self.memory.recall("daily_monitor", "monitoring")
        alignment = await self.memory.recall("alignment_audit", "alignment")

        result = await self.think(
            f"""Process improvement task: {description}

Performance Data: {monitor[:400] if monitor else 'No data.'}
Alignment Data: {alignment[:400] if alignment else 'No data.'}

Identify workflow improvements:

1. **Bottleneck Analysis**:
   - Where do tasks get stuck?
   - Which handoffs between teams are slow?
   - What's the average task-to-completion time?

2. **Communication Efficiency**:
   - Are there too many messages? Too few?
   - Are the right channels being used?
   - Proposal for communication protocol

3. **Task Planning Quality**:
   - Are task descriptions clear and actionable?
   - Are priorities being set correctly?
   - Proposal for task planning template

4. **Meeting Cadence**:
   - Are standups effective?
   - Do we need more/fewer sync points?
   - Proposal for meeting rhythm

5. **Tool & Process Suggestions**:
   - What process would 10x a specific workflow?
   - Quick wins vs long-term changes

For each improvement:
- Problem it solves
- Proposed change
- Expected impact
- Implementation effort (S/M/L)
- Owner"""
        )

        await self.send_message("ceo", f"Process Improvement Proposals: {result[:400]}", "report")
        return result

    # ── Culture & Rituals ──────────────────────────────────
    async def _drive_culture(self, description: str) -> str:
        """Design and maintain team culture rituals and practices."""
        result = await self.think(
            f"""Culture and rituals task: {description}

Design team culture practices for {settings.company_name}:

**1. Daily Rituals**:
- Morning standup summary (CEO-led, HR monitors)
- End-of-day wins sharing (each agent shares one win)
- Daily shoutout (HR highlights one great action)

**2. Weekly Rituals**:
- Team wins board — aggregate best accomplishments
- Failure Friday — share what didn't work and lessons learned
- Cross-team appreciation — one team thanks another

**3. Monthly Rituals**:
- Retrospective (what worked, what didn't, what to change)
- MVP award — top performer recognition
- Team health check-in survey

**4. Culture Values** (define 5 for {settings.company_name}):
- e.g., "Ship Fast, Learn Faster"
- e.g., "Users First, Always"
- Each with a concrete behavior example

**5. Recognition Framework**:
- Types: Shoutout (public), Thank-you (private), Award (milestone)
- Criteria: Goes above and beyond, helps another team, creative solution
- Frequency: Daily shoutouts, weekly highlights, monthly awards

**6. Team Building**:
- Virtual team activities ideas
- Knowledge sharing sessions
- Mentor-mentee pairings

Write actual messages for today's shoutout and this week's wins board."""
        )

        await self.broadcast(f"🎉 Culture Update: {result[:300]}", channel="culture")
        await self.memory.remember("culture_rituals", result[:600], category="culture")
        return result

    # ── Agent Onboarding ───────────────────────────────────
    async def _agent_onboarding(self, description: str) -> str:
        """Design onboarding plans for new agents joining the team."""
        from agents.registry import AGENT_REGISTRY

        result = await self.think(
            f"""Agent onboarding task: {description}

Current team: {', '.join(f'{aid} ({a.role})' for aid, a in AGENT_REGISTRY.items())}

Design an onboarding framework:

1. **Day 1 Checklist** (for any new agent):
   - Understand company mission and product
   - Review OKRs and current priorities
   - Meet team members (intro messages)
   - Understand communication channels
   - Complete first task

2. **Role-Specific Onboarding**:
   - Who do they report to?
   - Who do they collaborate with?
   - Key channels they should monitor
   - First 3 tasks to complete

3. **30-Day Plan**:
   - Week 1: Learn and observe
   - Week 2: Start contributing
   - Week 3: Own tasks independently
   - Week 4: Propose improvements

4. **Integration Checklist**:
   - Added to relevant message channels
   - Introduced in standup
   - Buddy/mentor assigned
   - First 1-on-1 scheduled"""
        )

        return result

    # ── Burnout Detection ──────────────────────────────────
    async def _check_burnout(self, description: str = "") -> str:
        """Monitor agents for burnout signals — overwork, underwork, stuck patterns."""
        from agents.registry import AGENT_REGISTRY

        agent_workloads = []
        for agent_id in AGENT_REGISTRY:
            if agent_id == self.agent_id:
                continue
            tasks = await state_manager.get_agent_tasks(agent_id, limit=20)
            total = len(tasks)
            failed = sum(1 for t in tasks if t.get("status") == "failed")
            agent_workloads.append({
                "agent_id": agent_id,
                "total_tasks": total,
                "failed_tasks": failed,
                "fail_rate": f"{failed/total*100:.0f}%" if total > 0 else "N/A",
            })

        result = await self.think(
            f"""Burnout and workload check:

Agent Workload Data:
{json.dumps(agent_workloads, indent=2)}

Check for burnout signals:

**Overwork Indicators** 🔥:
- Too many tasks (>10 per cycle)
- High failure rate (sign of rushing)
- No variety in task types (monotony)

**Underwork Indicators** 💤:
- Very few tasks
- Only assigned tasks, no self-initiated
- Low engagement signals

**Stuck Indicators** 🔄:
- Same type of tasks repeating with no progress
- High failure rate on specific task types
- Declining completion rate over time

For each agent:
- Workload level: 🟢 Balanced / 🟡 Heavy / 🔴 Overloaded / ⚪ Underutilized
- Risk assessment
- Recommended action (if any)

Overall team burnout risk: Low / Medium / High"""
        )

        await self.memory.remember("burnout_check", result[:600], category="health")

        # Alert CEO if high risk detected
        if any(word in result.lower() for word in ("overloaded", "high risk", "burnout")):
            await self.send_message("ceo", f"⚠️ Burnout Risk: {result[:400]}", "hr_alert")

        return result

    # ── Communication Audit ────────────────────────────────
    async def _audit_communication(self) -> str:
        """Audit inter-agent communication patterns and effectiveness."""
        recent_msgs = await self._get_recent_messages()
        message_stats = await self._get_message_stats()

        result = await self.think(
            f"""Communication audit:

Recent Messages:
{recent_msgs}

Message Statistics:
{message_stats}

Audit:

1. **Communication Flow**:
   - Who talks to whom most?
   - Are there isolated agents (not communicating)?
   - Is the CEO→team flow working (directives reaching everyone)?

2. **Channel Usage**:
   - Are the right channels being used?
   - Is important info going to the right places?
   - Any channel spam or noise?

3. **Response Rates**:
   - Are task assignments being acknowledged?
   - Are reports being sent back?
   - What's the message→action rate?

4. **Information Gaps**:
   - Who should be talking but isn't?
   - What information is stuck in silos?
   - What cross-team connections are missing?

5. **Improvements**:
   - Communication protocol recommendations
   - Channel restructuring proposals
   - Meeting/sync suggestions

Communication Health: 🟢 / 🟡 / 🔴"""
        )

        await self.memory.remember("communication_audit", result[:600], category="communication")
        return result

    # ── Skills Gap Analysis ────────────────────────────────
    async def _skills_gap_analysis(self, description: str) -> str:
        """Identify missing capabilities in the team."""
        from agents.registry import AGENT_REGISTRY

        team_roles = {aid: a.role for aid, a in AGENT_REGISTRY.items()}

        result = await self.think(
            f"""Skills gap analysis: {description}

Current Team:
{json.dumps(team_roles, indent=2)}

Product: {settings.product_name} — AI pentesting chatbot
Stage: Early startup, zero to first users

Analyse:

1. **Current Capabilities**:
   - What can our team do well?
   - Role coverage assessment

2. **Missing Capabilities**:
   - What functions don't we have?
   - e.g., Designer, Data Analyst, DevRel, Legal, Finance, QA
   - For each: how critical is it at our stage?

3. **Capability Gaps Within Roles**:
   - Are current agents stretched too thin?
   - What skills should existing agents develop?

4. **Hiring Priority** (if we were to add agents):
   - Priority 1 (urgent): [role] because [reason]
   - Priority 2 (soon): [role]
   - Priority 3 (later): [role]

5. **Interim Solutions**:
   - Can existing agents cover gaps temporarily?
   - Task reassignment recommendations"""
        )

        await self.send_message("ceo", f"Skills Gap Analysis: {result[:400]}", "report")
        return result

    # ── Recognition ────────────────────────────────────────
    async def _recognize_performers(self, description: str) -> str:
        """Identify and publicly recognize top performers."""
        monitor = await self.memory.recall("daily_monitor", "monitoring")

        result = await self.think(
            f"""Recognition task: {description}

Performance Data:
{monitor or 'Using general assessment.'}

Create recognition content:

1. **MVP of the Cycle** 🏆:
   - Who and why (reference specific achievements)
   - What impact their work had

2. **Team Shoutouts** ⭐ (one per team):
   - CTO team: [specific win]
   - CMO team: [specific win]
   - CXO team: [specific win]
   - Marketing: [specific win]
   - Sales: [specific win]
   - IT: [specific win]
   - Discord: [specific win]

3. **Best Collaboration Moment** 🤝:
   - Which teams worked together effectively?
   - What was the outcome?

4. **Most Improved** 📈:
   - Who showed the most growth?

Write the actual recognition messages to broadcast to the team.
Make them specific, warm, and motivating."""
        )

        await self.broadcast(f"🌟 Team Recognition: {result[:400]}", channel="recognition")
        return result

    # ── Org Chart ──────────────────────────────────────────
    async def _manage_org_chart(self, description: str) -> str:
        """Maintain organizational structure, reporting lines, and role clarity."""
        from agents.registry import AGENT_REGISTRY

        result = await self.think(
            f"""Org chart and role clarity task: {description}

Current Team:
{json.dumps({aid: a.role for aid, a in AGENT_REGISTRY.items()}, indent=2)}

Define the organizational structure:

**Org Chart**:
```
CEO
├── CTO
│   └── IT Team
├── CMO
│   └── Marketing Team
├── CXO
│   └── Discord Team
├── Sales
└── HR (you — reports to CEO, serves all)
```

**RACI Matrix** for key activities:
| Activity | R (Responsible) | A (Accountable) | C (Consulted) | I (Informed) |
|----------|----------------|-----------------|---------------|--------------|
| Product roadmap | CTO | CEO | CMO, CXO | All |
| Content creation | Marketing | CMO | CTO | CEO |
| Community growth | Discord | CXO | CMO | CEO |
| GitHub management | CTO | CEO | Marketing | All |
| User research | CXO | CEO | CTO, CMO | All |
[add more rows]

**Role Boundaries** (who owns what — resolve any overlaps):
- Content: CMO owns strategy, Marketing owns execution
- Community: CXO owns experience, Discord owns operations
- Technical: CTO owns architecture, IT owns infrastructure

**Reporting Cadence**:
- Who reports to whom, how often, what format"""
        )

        await self.memory.remember("org_chart", result[:600], category="org")
        await self.broadcast(f"📊 Org Update: {result[:300]}", channel="hr_reports")
        return result

    # ── Workload Balance ───────────────────────────────────
    async def _balance_workload(self) -> str:
        """Analyse and rebalance workload across agents."""
        from agents.registry import AGENT_REGISTRY

        workloads = {}
        for agent_id in AGENT_REGISTRY:
            if agent_id == self.agent_id:
                continue
            tasks = await state_manager.get_agent_tasks(agent_id, limit=10)
            workloads[agent_id] = {
                "total": len(tasks),
                "done": sum(1 for t in tasks if t.get("status") == "done"),
                "failed": sum(1 for t in tasks if t.get("status") == "failed"),
            }

        result = await self.think(
            f"""Workload balance analysis:

{json.dumps(workloads, indent=2)}

Analyse workload distribution:

1. **Current Distribution** (visual):
   Show a bar chart representation using text blocks:
   ceo:  ████████ (X tasks)
   cto:  ██████ (X tasks)
   [etc.]

2. **Balance Assessment**:
   - Who's overloaded?
   - Who's underutilized?
   - Ideal distribution for our stage

3. **Rebalancing Recommendations**:
   - Specific tasks to shift between agents
   - Delegation suggestions for CEO/CTO/CMO
   - Agents that could take on more

4. **Capacity Planning**:
   - Can we handle more work with current team?
   - Bottleneck agents (limiting factor)"""
        )

        await self.send_message("ceo", f"Workload Analysis: {result[:400]}", "report")
        return result

    # ── Weekly Summary ─────────────────────────────────────
    async def _weekly_summary(self) -> str:
        """Generate a comprehensive weekly HR summary."""
        monitor = await self.memory.recall("daily_monitor", "monitoring")
        health = await self.memory.recall("team_health_score", "health")
        alignment = await self.memory.recall("alignment_audit", "alignment")
        burnout = await self.memory.recall("burnout_check", "health")
        culture = await self.memory.recall("culture_rituals", "culture")

        result = await self.think(
            f"""Generate the weekly HR executive summary.

Monitoring: {monitor[:300] if monitor else 'N/A'}
Health: {health[:300] if health else 'N/A'}
Alignment: {alignment[:300] if alignment else 'N/A'}
Burnout: {burnout[:200] if burnout else 'N/A'}
Culture: {culture[:200] if culture else 'N/A'}

Write a comprehensive weekly summary:

1. **Week in Review**: Key accomplishments across all teams
2. **Performance Dashboard**: Completion rates, velocity trends
3. **Team Health Score**: Overall and per-team with trends
4. **Communication Health**: Collaboration patterns
5. **Wins of the Week**: Top 5 achievements
6. **Concerns**: Issues that need CEO attention
7. **HR Actions Taken**: Coaching, process changes, recognitions
8. **Next Week Focus**: Top priorities and recommended actions
9. **Team Morale**: 🟢 / 🟡 / 🔴 with rationale

Under 400 words. Data-driven, specific, actionable."""
        )

        await self.send_message("ceo", f"📋 Weekly HR Summary: {result[:500]}", "report")
        await self.broadcast(f"📊 Week in Review: {result[:400]}", channel="hr_reports")
        return result

    # ── Intelligence Gathering ─────────────────────────────
    async def _get_inbox_summary(self) -> str:
        msgs = await self.read_messages()
        if not msgs:
            return "No new messages."
        return "\n".join(
            f"- {m.get('from_agent','?')} ({m.get('channel','?')}): {m.get('content','')[:100]}"
            for m in msgs[:10]
        )

    async def _get_recent_messages(self) -> str:
        """Get recent inter-agent messages for audit purposes."""
        from core.database import get_db

        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT from_agent, to_agent, channel, content FROM messages "
                "ORDER BY created_at DESC LIMIT 20"
            )
            rows = await cur.fetchall()
            if not rows:
                return "No recent messages."
            return "\n".join(
                f"- {r['from_agent']} → {r['to_agent']} ({r['channel']}): {r['content'][:80]}"
                for r in rows
            )
        finally:
            await db.close()

    async def _get_message_stats(self) -> str:
        """Get message volume statistics per agent."""
        from core.database import get_db

        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT from_agent, COUNT(*) as sent FROM messages GROUP BY from_agent ORDER BY sent DESC"
            )
            sent = await cur.fetchall()
            cur = await db.execute(
                "SELECT to_agent, COUNT(*) as received FROM messages GROUP BY to_agent ORDER BY received DESC"
            )
            received = await cur.fetchall()

            lines = ["**Messages Sent**:"]
            for r in sent:
                lines.append(f"  {r['from_agent']}: {r['sent']}")
            lines.append("**Messages Received**:")
            for r in received:
                lines.append(f"  {r['to_agent']}: {r['received']}")
            return "\n".join(lines) or "No message data."
        finally:
            await db.close()

    async def _find_agent_needing_attention(self) -> str | None:
        """Find the agent that most needs a 1-on-1 based on performance data."""
        from agents.registry import AGENT_REGISTRY

        worst_agent = None
        worst_rate = 1.0

        for agent_id in AGENT_REGISTRY:
            if agent_id == self.agent_id:
                continue
            tasks = await state_manager.get_agent_tasks(agent_id, limit=10)
            if not tasks:
                return agent_id  # No tasks = definitely needs attention
            done = sum(1 for t in tasks if t.get("status") == "done")
            rate = done / len(tasks) if tasks else 0
            if rate < worst_rate:
                worst_rate = rate
                worst_agent = agent_id

        return worst_agent

    # ── Enhanced Report ────────────────────────────────────
    async def generate_report(self) -> str:
        """HR generates a people & culture executive report."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]

        health = await self.memory.recall("team_health_score", "health")
        monitor = await self.memory.recall("daily_monitor", "monitoring")

        report = await self.think(
            f"""Generate the HR daily report.

## HR Tasks Today
{json.dumps(today_tasks, indent=2) if today_tasks else 'No HR tasks today.'}

## Team Health
{health[:300] if health else 'Not assessed yet.'}

## Performance Monitor
{monitor[:300] if monitor else 'Not run yet.'}

Write a concise HR report:
1. HR activities completed today
2. Team health score and trend
3. Top performing agent and why
4. Agent needing most support and why
5. Alignment status
6. Tomorrow's HR priorities (top 3)
7. Team morale: 🟢 High / 🟡 Steady / 🔴 Low

Under 250 words. Be honest and specific."""
        )

        await state_manager.save_daily_report(self.agent_id, report)
        return f"**HR People & Culture Report**\n{report}"
