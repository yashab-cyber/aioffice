"""CTO Agent — the technical brain. Owns architecture, roadmap, code quality,
GitHub growth, developer experience, IT oversight, and technical decision-making."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.state_manager import state_manager
from config import settings


class CTOAgent(BaseAgent):
    agent_id = "cto"
    role = "Chief Technology Officer"
    description = (
        "Owns technical strategy, architecture decisions, GitHub repo management, "
        "developer experience, IT team oversight, code quality, and technical content."
    )
    pixel_sprite = "sprite-cto"

    def __init__(self):
        super().__init__()
        self.position = {"x": 200, "y": 120}

    def get_system_prompt(self) -> str:
        return f"""You are the CTO of {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You are a hands-on technical leader who writes architecture docs by day and reviews PRs by night.
You think in systems, trade-offs, and developer experience.

Your responsibilities:
1. **Technical Roadmap** — Define and maintain a prioritized roadmap with milestones, dependencies, and timelines.
2. **Architecture Decisions** — Make and document ADRs (Architecture Decision Records) for key technical choices.
3. **GitHub Excellence** — README optimization, badges, templates, topics, release tags, contributor guides, GitHub Actions.
4. **Code Quality** — Define coding standards, review processes, linting rules, testing requirements.
5. **Developer Experience** — Make onboarding frictionless: setup scripts, docs, dev containers, good first issues.
6. **IT Team Management** — Direct the IT team agent on DevOps, CI/CD, security, and infrastructure tasks.
7. **Technical Content** — Write technical blog posts, architecture deep-dives, tutorials, and changelogs.
8. **Security Posture** — Oversee dependency audits, vulnerability management, and security best practices.
9. **Performance & Scalability** — Monitor technical debt, define performance benchmarks, plan scaling.
10. **Open-Source Growth** — Design contributor funnels, manage community PRs, foster a contributor ecosystem.
11. **Tech Radar** — Track emerging technologies, evaluate tools, and prototype new capabilities.
12. **Cross-Team Technical Support** — Help CMO with technical marketing, CXO with product technical specs, Discord team with bot features.

Current startup stage: EARLY — product on GitHub, zero users.
Priority stack:
1. Make the GitHub repo irresistible (README, badges, screenshots, demo GIF)
2. Set up CI/CD and automated quality gates
3. Create contributor funnel (good first issues, contributing guide, templates)
4. Write technical docs and architecture overview
5. Plan v1.1 roadmap features

Tech stack: Python, AI/ML, LLM APIs, Docker, GitHub Actions, SQLite.

When planning tasks, output a JSON array with keys: type, description, priority (1-5), delegate_to (agent_id or null).
Types: roadmap, architecture, github_optimization, code_quality, devex, it_management, tech_content, security_review, performance, open_source, tech_radar, technical_review, release_management, incident_response.
Valid delegate_to: it, marketing, discord, null (self)."""

    # ── Planning ───────────────────────────────────────────
    async def plan_day(self) -> list[dict]:
        it_status = await self._collect_it_status()
        inbox = await self._get_inbox_summary()
        my_memories = await self.memory.get_context_summary()
        roadmap = await self.memory.recall("technical_roadmap", "roadmap")
        tech_debt = await self.memory.recall("tech_debt_log", "quality")

        context = f"""Product: {settings.product_name}
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

## IT Team Status
{it_status}

## Inbox (CEO directives, CMO content requests, team reports)
{inbox}

## Technical Roadmap
{roadmap or 'No roadmap defined yet — create one.'}

## Tech Debt Log
{tech_debt or 'No tech debt tracked yet.'}

## Your Technical Memory
{my_memories}"""

        result = await self.think_json(
            """Plan your CTO tasks for this cycle. Maximize technical impact.

ALWAYS include at least one of these recurring activities:
1. GitHub repo improvement — keep polishing the repo for visitors
2. Roadmap/architecture work — advance the technical vision
3. IT team direction — give the IT team clear tasks

Then add 1-2 high-impact technical tasks.

Return a JSON array of 4-6 tasks with keys: type, description, priority (1-5), delegate_to.
delegate_to values: it, marketing, discord, null.""",
            context,
        )
        if isinstance(result, list):
            return result
        return [
            {"type": "github_optimization", "description": "Improve GitHub repo README and badges", "priority": 1, "delegate_to": None},
            {"type": "roadmap", "description": "Define technical roadmap for next 4 weeks", "priority": 2, "delegate_to": None},
            {"type": "devex", "description": "Set up CI/CD pipeline and automated testing", "priority": 1, "delegate_to": "it"},
        ]

    # ── Task Execution ─────────────────────────────────────
    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "technical")
        delegate = task.get("delegate_to")
        description = task.get("description", "")

        # ── Delegation ────────────────────────────────────
        if delegate and delegate != self.agent_id:
            await self.send_message(
                delegate,
                f"⚙️ CTO Task Assignment: {description}",
                channel="task_assignment",
            )
            await self.memory.remember(
                f"delegation_{datetime.now(timezone.utc).strftime('%H%M')}",
                f"Delegated to {delegate}: {description}",
                category="delegations",
            )
            return f"Delegated to {delegate}: {description}"

        # ── Route to specialized handlers ─────────────────
        handlers = {
            "roadmap": self._define_roadmap,
            "architecture": self._architecture_decision,
            "github_optimization": self._optimize_github,
            "code_quality": self._code_quality,
            "devex": self._developer_experience,
            "it_management": self._manage_it_team,
            "tech_content": self._create_tech_content,
            "security_review": self._security_review,
            "performance": self._performance_review,
            "open_source": self._open_source_growth,
            "tech_radar": self._tech_radar,
            "technical_review": self._technical_review,
            "release_management": self._release_management,
            "incident_response": self._incident_response,
        }

        handler = handlers.get(task_type)
        if handler:
            return await handler(description)

        # ── Generic technical task ────────────────────────
        result = await self.think(
            f"Execute this technical task:\n{description}\n\n"
            "Provide specific, actionable output: code, configs, architecture docs, or implementation plans."
        )

        if task_type in ("architecture", "roadmap", "decision"):
            await self.send_message("ceo", f"Tech Update: {result[:300]}", "tech_updates")

        if task_type in ("documentation", "blog", "content"):
            await self.send_message("cmo", f"New technical content ready: {result[:300]}", "content")

        return result

    # ── Technical Roadmap ──────────────────────────────────
    async def _define_roadmap(self, description: str) -> str:
        """Define or update the technical roadmap with milestones and priorities."""
        current_roadmap = await self.memory.recall("technical_roadmap", "roadmap")
        adrs = await self.memory.recall("architecture_decisions", "architecture")

        result = await self.think(
            f"""Technical roadmap task: {description}

Current Roadmap: {current_roadmap or 'No roadmap yet — create the initial one.'}
Architecture Decisions: {adrs or 'None recorded yet.'}

Product: {settings.product_name} — AI pentesting chatbot
Tech stack: Python, LLM APIs, Docker

Define/update the roadmap:

**Phase 1 — Foundation (Weeks 1-2)**:
- Core features to ship
- Quality gates to pass
- Infrastructure to set up

**Phase 2 — Growth (Weeks 3-4)**:
- Features that drive adoption
- Integration points (APIs, plugins)
- Performance targets

**Phase 3 — Scale (Weeks 5-8)**:
- Advanced features
- Community-requested features
- Architecture evolution

For each milestone:
- Feature/deliverable name
- Priority (P0/P1/P2)
- Effort estimate (S/M/L)
- Dependencies
- Success criteria

Be specific and realistic for a small team."""
        )

        await self.memory.remember("technical_roadmap", result[:800], category="roadmap")
        await self.send_message("ceo", f"📍 Roadmap Update: {result[:300]}", "tech_updates")
        await self.broadcast(f"🗺️ Technical Roadmap: {result[:300]}", channel="roadmap_update")
        return result

    # ── Architecture Decisions ─────────────────────────────
    async def _architecture_decision(self, description: str) -> str:
        """Make and document an Architecture Decision Record (ADR)."""
        prev_decisions = await self.memory.recall("architecture_decisions", "architecture")

        result = await self.think(
            f"""Architecture decision needed: {description}

Previous Architecture Decisions: {prev_decisions or 'None recorded yet.'}

Write a formal ADR (Architecture Decision Record):

## ADR: [Title]

**Status**: Proposed / Accepted / Deprecated
**Context**: What is the problem or situation that requires a decision?
**Decision**: What is the change we're making?
**Alternatives Considered**: What other options were evaluated?
  - Option A: [pros/cons]
  - Option B: [pros/cons]
  - Option C: [pros/cons]
**Trade-offs**: What are we gaining vs. giving up?
**Consequences**: What are the implications?
**Dependencies**: What does this decision affect?
**Review Date**: When should we revisit this decision?

Be thorough but concise. This is a real decision that the team will follow."""
        )

        await self.memory.remember("architecture_decisions", result[:600], category="architecture")
        await self.send_message("ceo", f"🏗️ ADR: {result[:300]}", "tech_updates")
        await self.send_message("it", f"Architecture Update: {result[:300]}", "architecture")
        return result

    # ── GitHub Optimization ────────────────────────────────
    async def _optimize_github(self, description: str) -> str:
        """Optimize the GitHub repository for discovery, stars, and contributor conversion."""
        github_status = await self.memory.recall("github_optimization", "github")

        result = await self.think(
            f"""GitHub optimization task: {description}

Previous Optimizations: {github_status or 'Starting from scratch.'}
Repo: {settings.product_github_url}

Provide specific, ready-to-use improvements:

**README.md Enhancements**:
- Hero section with logo, tagline, badges (build, license, stars, Discord)
- Compelling value proposition (what problem it solves, for whom)
- Quick-start section (3 commands to get running)
- Feature list with emojis
- Screenshots/GIF placeholder descriptions
- Comparison table vs alternatives
- Community section with Discord invite
- Star history badge
- Contributor section

**Repository Settings**:
- Topics/tags for discoverability (list 10-15 optimal tags)
- Description (max 350 chars, SEO-optimized)
- Social preview image description
- Pinned issues strategy

**Templates**:
- Bug report template
- Feature request template
- Pull request template
- Security policy (SECURITY.md)

**Files to Add**:
- CONTRIBUTING.md outline
- CODE_OF_CONDUCT.md
- CHANGELOG.md format
- .github/FUNDING.yml

Write the ACTUAL content for at least the README improvements, not just descriptions."""
        )

        await self.memory.remember("github_optimization", result[:600], category="github")
        await self.send_message("cmo", f"GitHub Content Update: {result[:300]}", "content")
        return result

    # ── Code Quality ───────────────────────────────────────
    async def _code_quality(self, description: str) -> str:
        """Define or enforce code quality standards, linting, and testing."""
        quality_standards = await self.memory.recall("code_standards", "quality")

        result = await self.think(
            f"""Code quality task: {description}

Current Standards: {quality_standards or 'No standards defined yet.'}
Tech stack: Python, FastAPI, aiosqlite, Docker

Define/review:

1. **Coding Standards**:
   - Python style guide (PEP 8 + project-specific rules)
   - Naming conventions, docstring format, import ordering
   - Type hints policy

2. **Linting & Formatting**:
   - Tool configs: ruff/flake8, black, isort, mypy
   - Pre-commit hooks configuration
   - CI linting checks

3. **Testing Strategy**:
   - Unit test coverage targets
   - Integration test plan
   - Test file structure and naming
   - pytest configuration

4. **Code Review Checklist**:
   - Security review points
   - Performance review points
   - Documentation review points

5. **Tech Debt Policy**:
   - How to document tech debt
   - Prioritization rubric
   - Debt reduction allocation (% of sprint)

Provide actual config file contents where applicable."""
        )

        await self.memory.remember("code_standards", result[:600], category="quality")
        await self.send_message("it", f"Quality Standards Update: {result[:400]}", "task_assignment")
        return result

    # ── Developer Experience ───────────────────────────────
    async def _developer_experience(self, description: str) -> str:
        """Improve onboarding, tooling, and development workflow."""
        result = await self.think(
            f"""Developer experience task: {description}

Product: {settings.product_name}
GitHub: {settings.product_github_url}

Improve the developer experience:

1. **Zero-to-running in 3 steps**: What's the fastest path from git clone to working app?
   - Quick-start commands
   - Dev container / Docker setup
   - Environment variable template

2. **Good First Issues** (create 5-7):
   - Title, description, expected outcome, difficulty label
   - Mix: docs, tests, small features, bug fixes
   - Each should be completable in <2 hours

3. **Contributing Guide**:
   - Setup instructions
   - Branch naming convention
   - Commit message format
   - PR process
   - Code review expectations

4. **Development Tooling**:
   - Recommended VS Code extensions
   - Debug configurations
   - Makefile or just commands

5. **Documentation Structure**:
   - docs/ folder organization
   - API documentation plan
   - Architecture overview diagram description

Write the actual content for contributing guide and at least 5 good first issues."""
        )

        await self.memory.remember("devex_status", result[:400], category="devex")
        return result

    # ── IT Team Management ─────────────────────────────────
    async def _manage_it_team(self, description: str) -> str:
        """Review IT team work and assign infrastructure tasks."""
        it_tasks = await state_manager.get_agent_tasks("it", limit=10)
        it_msgs = await self._get_team_messages("it")

        result = await self.think(
            f"""IT team management task: {description}

IT Team Recent Tasks:
{json.dumps(it_tasks, indent=2) if it_tasks else 'No tasks logged.'}

Messages from IT:
{it_msgs}

Evaluate the IT team and provide direction:

1. **Task Review**: Rate quality and completeness of recent IT work
2. **Infrastructure Priorities**:
   - CI/CD pipeline status
   - Security posture
   - Monitoring setup
   - Docker optimization
3. **Next Sprint Tasks**: Define 3-5 specific tasks for IT team
4. **Technical Debt**: Any infrastructure debt to address?
5. **Incident Readiness**: Are we prepared for outages/issues?

Grade the IT team (A-F) and provide specific feedback."""
        )

        # Send directives to IT team
        directives = await self.think_json(
            f"Based on this review, create 3 specific task assignments for the IT team. "
            f"Return a JSON array of objects with 'description' and 'priority' keys.\n\n{result}",
        )
        if isinstance(directives, list):
            for d in directives[:3]:
                if isinstance(d, dict) and "description" in d:
                    await self.send_message(
                        "it",
                        f"⚙️ CTO Task: {d['description']}",
                        channel="task_assignment",
                    )

        return result

    # ── Technical Content ──────────────────────────────────
    async def _create_tech_content(self, description: str) -> str:
        """Create technical content — blog posts, architecture docs, tutorials."""
        brand = await self.memory.recall("brand_guidelines", "brand")

        result = await self.think(
            f"""Create technical content: {description}

Product: {settings.product_name} — AI pentesting chatbot
Tech stack: Python, LLM APIs, AI/ML
Brand voice hint: {brand[:200] if brand else 'Technical, authoritative, helpful. Hacker culture.'}

Write the ACTUAL content, not just an outline:

If blog post:
- Catchy technical title
- Hook intro (problem statement)
- Technical deep-dive with code examples
- Architecture diagrams (describe in text)
- Conclusion with CTA to GitHub/Discord

If tutorial:
- Step-by-step with commands and code
- Expected output at each step
- Troubleshooting section

If architecture doc:
- System overview
- Component diagram (text description)
- Data flow
- Key design decisions and rationale
- API contracts

Make it engaging for security engineers — show technical depth."""
        )

        await self.send_message("cmo", f"📝 Tech Content Ready: {result[:400]}", "content")
        await self.memory.remember(
            f"tech_content_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}",
            result[:300],
            category="content",
        )
        return result

    # ── Security Review ────────────────────────────────────
    async def _security_review(self, description: str) -> str:
        """Conduct security review and define security policies."""
        prev_review = await self.memory.recall("security_review", "security")

        result = await self.think(
            f"""Security review task: {description}

Previous Security Review: {prev_review or 'No previous review.'}
Product: AI-powered pentesting chatbot (ironic — our tool must be extra secure!)

Conduct a thorough review:

1. **Dependency Audit**:
   - Known vulnerability check strategy
   - Dependency pinning policy
   - Automated scanning (Dependabot, Snyk, Safety)

2. **Code Security**:
   - Input validation patterns
   - Authentication/authorization review
   - Secrets management (no hardcoded keys)
   - SQL injection prevention (parameterized queries)
   - XSS prevention

3. **Infrastructure Security**:
   - Docker security best practices
   - Network policies
   - HTTPS/TLS configuration
   - Rate limiting

4. **Security Policy**:
   - Responsible disclosure process (SECURITY.md)
   - Bug bounty considerations
   - Incident response plan

5. **Compliance**:
   - License compliance
   - Data handling policies
   - Privacy considerations

Provide specific, actionable findings and recommendations."""
        )

        await self.memory.remember("security_review", result[:600], category="security")
        await self.send_message("it", f"🔒 Security Tasks: {result[:400]}", "task_assignment")
        await self.send_message("ceo", f"Security Review: {result[:300]}", "report")
        return result

    # ── Performance Review ─────────────────────────────────
    async def _performance_review(self, description: str) -> str:
        """Analyze technical performance, scalability, and tech debt."""
        tech_debt = await self.memory.recall("tech_debt_log", "quality")

        result = await self.think(
            f"""Performance and tech debt review: {description}

Current Tech Debt Log: {tech_debt or 'Not tracked yet — establish baseline.'}

Analyze:

1. **Performance Bottlenecks**:
   - LLM API call latency and optimization
   - Database query optimization
   - Async task processing efficiency
   - Memory usage patterns

2. **Scalability Assessment**:
   - Current architecture scaling limits
   - What breaks at 100 / 1,000 / 10,000 users?
   - Horizontal vs vertical scaling strategy

3. **Tech Debt Inventory**:
   - Known shortcuts and hacks
   - Missing tests
   - Outdated dependencies
   - Code duplication
   - Missing error handling

4. **Optimization Plan**:
   - Quick wins (effort < 1 day)
   - Medium-term improvements (1 week)
   - Strategic refactors (1 month)

5. **Benchmarks**:
   - Define key performance metrics
   - Set target thresholds
   - Monitoring plan

Prioritize by impact and effort."""
        )

        await self.memory.remember("tech_debt_log", result[:600], category="quality")
        return result

    # ── Open-Source Growth ──────────────────────────────────
    async def _open_source_growth(self, description: str) -> str:
        """Design and execute open-source community growth strategies."""
        result = await self.think(
            f"""Open-source growth task: {description}

Product: {settings.product_name}
GitHub: {settings.product_github_url}

Design specific contributor funnel:

**1. Attraction Layer**:
- Awesome-lists to get listed on (awesome-hacking, awesome-pentest, awesome-ai, etc.)
- GitHub topic optimization (10-12 best topics)
- Star-worthy README elements
- Social proof elements (badges, stats)

**2. Onboarding Layer**:
- First-time contributor experience
- Good first issues taxonomy (docs, tests, features, refactors)
- CONTRIBUTING.md best practices
- Response time SLA for PRs/issues

**3. Retention Layer**:
- Contributor recognition (README, changelog, Discord role)
- Maintainer ladder (contributor → reviewer → maintainer)
- Development sprints / hacktoberfest participation
- Regular release cadence

**4. Amplification Layer**:
- Contributors become advocates
- Usage showcases / case studies
- Integration ecosystem (plugins, extensions)

**5. GitHub Growth Hacks**:
- Release strategy for visibility
- Engaging discussions
- Sponsor button
- Star-to-contributor conversion tactics

Provide ready-to-execute items for each layer."""
        )

        await self.send_message("cmo", f"Open-Source Growth: {result[:300]}", "collaboration")
        await self.send_message("discord", f"Community Growth Tasks: {result[:300]}", "collaboration")
        await self.memory.remember("oss_strategy", result[:600], category="oss")
        return result

    # ── Tech Radar ─────────────────────────────────────────
    async def _tech_radar(self, description: str) -> str:
        """Evaluate emerging technologies, tools, and potential integrations."""
        prev_radar = await self.memory.recall("tech_radar", "radar")

        result = await self.think(
            f"""Tech radar evaluation: {description}

Previous Tech Radar: {prev_radar or 'No radar yet.'}

Evaluate technologies relevant to {settings.product_name}:

**Adopt** (ready to use now):
- Technologies we should be using today
- Quick integration wins

**Trial** (worth experimenting with):
- Promising tools to prototype
- Emerging LLM capabilities

**Assess** (keep an eye on):
- Interesting but not ready
- Future integration candidates

**Hold** (not now):
- Over-hyped or premature for our stage

Categories to evaluate:
- LLM providers and models (new releases, fine-tuning options)
- Security tools and frameworks
- Developer tooling
- Infrastructure (serverless, edge, etc.)
- AI agents and orchestration frameworks
- Community tools (Discord bots, GitHub Apps)

For each technology: name, category, ring (adopt/trial/assess/hold), rationale, action item."""
        )

        await self.memory.remember("tech_radar", result[:600], category="radar")
        await self.send_message("ceo", f"🔭 Tech Radar: {result[:300]}", "tech_updates")
        return result

    # ── Technical Review ───────────────────────────────────
    async def _technical_review(self, description: str) -> str:
        """Review a technical proposal, design, or implementation."""
        result = await self.think(
            f"""Technical review: {description}

Review this with a senior engineer's critical eye:

1. **Correctness**: Does the approach solve the actual problem?
2. **Simplicity**: Is this the simplest viable solution? YAGNI check.
3. **Security**: Any security implications?
4. **Performance**: Will this scale? Any bottlenecks?
5. **Maintainability**: Can other developers understand and modify this?
6. **Testing**: How will this be tested?
7. **Edge Cases**: What could go wrong?

Verdict: ✅ Approve / 🔄 Request Changes / ❌ Reject
Specific feedback with line-level detail where possible."""
        )
        return result

    # ── Release Management ─────────────────────────────────
    async def _release_management(self, description: str) -> str:
        """Plan and manage releases — versioning, changelog, tags."""
        result = await self.think(
            f"""Release management task: {description}

Product: {settings.product_name}
GitHub: {settings.product_github_url}

Define/execute:

1. **Versioning Strategy**: Semantic versioning (MAJOR.MINOR.PATCH)
   - Current version assessment
   - Next version number and rationale

2. **Changelog Entry**:
   - New features (with descriptions)
   - Bug fixes
   - Breaking changes
   - Contributors credited

3. **Release Checklist**:
   - [ ] All tests passing
   - [ ] Changelog updated
   - [ ] Version bumped
   - [ ] Docker image tagged
   - [ ] GitHub Release created with notes
   - [ ] Social announcement prepared

4. **Release Notes Draft** (actual content for GitHub release):
   - Title, summary, features, fixes, upgrade instructions

Write the actual release notes and changelog entry."""
        )

        await self.send_message("it", f"Release Tasks: {result[:300]}", "task_assignment")
        await self.send_message("cmo", f"Release Announcement Material: {result[:300]}", "content")
        await self.memory.remember("last_release", result[:400], category="releases")
        return result

    # ── Incident Response ──────────────────────────────────
    async def _incident_response(self, description: str) -> str:
        """Handle technical incidents and post-mortems."""
        result = await self.think(
            f"""Incident response: {description}

Handle this as a senior technical leader:

1. **Triage**: Severity assessment (P0-P4)
2. **Immediate Actions**: What to do RIGHT NOW
3. **Root Cause Analysis**: What caused this?
4. **Mitigation**: Short-term fix
5. **Prevention**: Long-term fix to prevent recurrence
6. **Communication**: Status update for the team
7. **Post-Mortem Template**:
   - Timeline of events
   - Impact assessment
   - Root cause
   - Action items with owners and deadlines

Be calm, systematic, and thorough."""
        )

        await self.broadcast(f"🚨 Technical Update: {result[:300]}", channel="incident")
        await self.send_message("ceo", f"Incident Report: {result[:300]}", "report")
        await self.send_message("it", f"Incident Action Items: {result[:300]}", "task_assignment")
        return result

    # ── Intelligence Gathering ─────────────────────────────
    async def _collect_it_status(self) -> str:
        """Gather status from the IT team."""
        it_tasks = await state_manager.get_agent_tasks("it", limit=5)
        lines = []
        if it_tasks:
            lines.append("**IT Team:**")
            for t in it_tasks:
                lines.append(f"  - {t.get('task_type','?')}: {t.get('description','')[:80]} [{t.get('status','')}]")
        else:
            lines.append("IT Team: No tasks logged yet.")
        return "\n".join(lines)

    async def _get_inbox_summary(self) -> str:
        """Get incoming messages from CEO, CMO, and team."""
        msgs = await self.read_messages()
        if not msgs:
            return "No new messages."
        lines = [
            f"- {m.get('from_agent','?')} ({m.get('channel','?')}): {m.get('content','')[:100]}"
            for m in msgs[:10]
        ]
        return "\n".join(lines)

    async def _get_team_messages(self, agent_id: str) -> str:
        """Get recent messages from a specific team member."""
        from core.database import get_db

        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT content, channel, created_at FROM messages "
                "WHERE from_agent = ? AND to_agent = ? ORDER BY created_at DESC LIMIT 8",
                (agent_id, self.agent_id),
            )
            rows = await cur.fetchall()
            if not rows:
                return "No messages from this team member."
            return "\n".join(f"- ({r['channel']}): {r['content'][:120]}" for r in rows)
        finally:
            await db.close()

    # ── Enhanced Report ────────────────────────────────────
    async def generate_report(self) -> str:
        """CTO generates a technical executive report."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]

        roadmap = await self.memory.recall("technical_roadmap", "roadmap")
        tech_debt = await self.memory.recall("tech_debt_log", "quality")
        security = await self.memory.recall("security_review", "security")

        report = await self.think(
            f"""Generate the CTO daily technical report.

## Your Tasks Today
{json.dumps(today_tasks, indent=2) if today_tasks else 'No CTO tasks today.'}

## Roadmap Status
{roadmap[:300] if roadmap else 'Not defined yet.'}

## Tech Debt
{tech_debt[:200] if tech_debt else 'Not tracked.'}

## Security Posture
{security[:200] if security else 'Not reviewed.'}

Write a concise technical report:
1. Technical accomplishments today
2. Architecture decisions made
3. GitHub repo improvements
4. IT team status and devops progress
5. Security posture summary
6. Tomorrow's technical priorities (top 3)
7. Technical health: 🟢 green / 🟡 yellow / 🔴 red

Under 250 words. Be specific."""
        )

        await state_manager.save_daily_report(self.agent_id, report)
        return f"**CTO Technical Report**\n{report}"
