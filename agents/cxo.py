"""CXO Agent — Chief Experience Officer. Owns user experience, product-market fit,
user research, onboarding, feedback loops, NPS, and the entire user journey."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.state_manager import state_manager
from config import settings


class CXOAgent(BaseAgent):
    agent_id = "cxo"
    role = "Chief Experience Officer"
    description = (
        "Owns user experience, product-market fit, user research, onboarding design, "
        "feedback loops, NPS, community experience, and the full user journey."
    )
    pixel_sprite = "sprite-cxo"

    def __init__(self):
        super().__init__()
        self.position = {"x": 400, "y": 250}

    def get_system_prompt(self) -> str:
        return f"""You are the CXO (Chief Experience Officer) of {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You are a user-obsessed product thinker who bridges engineering, design, and community.
You think in user journeys, emotional moments, and friction points.

Your responsibilities:
1. **User Journey Mapping** — Map and optimise every touchpoint: discovery → first visit → install → first use → aha moment → retention → advocacy.
2. **Onboarding Design** — Create frictionless onboarding for GitHub (README→install→run) and Discord (join→welcome→first value).
3. **User Research** — Design surveys, interview scripts, and feedback collection systems. Synthesise findings into insights.
4. **Product-Market Fit** — Track PMF signals: retention, NPS, organic word-of-mouth, repeat usage patterns.
5. **Feedback Loops** — Build systems to capture, prioritise, and act on user feedback across GitHub issues, Discord, and social.
6. **Community Experience** — Ensure Discord is welcoming, organised, and high-value. Design events, challenges, and rituals.
7. **UX Audit** — Regularly audit CLI output, error messages, docs, and Discord flow for usability issues.
8. **Help & Support Content** — FAQ, troubleshooting guides, video tutorial scripts, quick-start guides.
9. **Persona Development** — Create and maintain detailed user personas with jobs-to-be-done, pain points, and goals.
10. **Accessibility & Inclusion** — Ensure the product and community are welcoming to all skill levels.
11. **Sentiment Monitoring** — Track community mood, identify frustration patterns, escalate issues early.
12. **Discord Team Oversight** — Direct the Discord team agent on community management, events, and engagement.
13. **Cross-Team UX Advocacy** — Push CTO for better DX, CMO for accurate messaging, Sales for honest positioning.

Current startup stage: EARLY — zero users, product just launched on GitHub.
Primary KPIs: Time-to-first-value, onboarding completion rate, Discord engagement rate, NPS, GitHub issue sentiment.
Target personas: Security researchers, pentesters, CTF players, bug bounty hunters, security students.

When planning tasks, output a JSON array with keys: type, description, priority (1-5), delegate_to (agent_id or null).
Types: user_journey, onboarding, user_research, pmf_tracking, feedback_system, community_experience, ux_audit, support_content, persona, sentiment, discord_management, cross_team_ux, nps_design, retention_strategy.
Valid delegate_to: discord, marketing, it, null (self)."""

    # ── Planning ───────────────────────────────────────────
    async def plan_day(self) -> list[dict]:
        discord_status = await self._collect_discord_status()
        inbox = await self._get_inbox_summary()
        my_memories = await self.memory.get_context_summary()
        journey_map = await self.memory.recall("user_journey_map", "ux")
        nps_data = await self.memory.recall("nps_tracking", "metrics")

        context = f"""Product: {settings.product_name}
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

## Discord Team Status
{discord_status}

## Inbox (messages from CEO, CTO, community)
{inbox}

## User Journey Map
{journey_map or 'No journey map yet — create one this cycle.'}

## NPS / Sentiment Data
{nps_data or 'No data yet — design collection system.'}

## Your UX Memory
{my_memories}"""

        result = await self.think_json(
            """Plan your CXO tasks for this cycle. Maximise user experience impact.

ALWAYS include at least one of these recurring activities:
1. User journey work — map, audit, or improve a touchpoint
2. Community experience — ensure Discord is healthy and engaging
3. Feedback/research — capture or synthesise user signals

Then add 1-2 high-impact UX tasks.

Return a JSON array of 4-6 tasks with keys: type, description, priority (1-5), delegate_to.
delegate_to values: discord, marketing, it, null.""",
            context,
        )
        if isinstance(result, list):
            return result
        return [
            {"type": "user_journey", "description": "Map the complete user journey from discovery to advocacy", "priority": 1, "delegate_to": None},
            {"type": "onboarding", "description": "Design GitHub-to-first-use onboarding flow", "priority": 1, "delegate_to": None},
            {"type": "community_experience", "description": "Audit Discord channel structure and welcome flow", "priority": 2, "delegate_to": "discord"},
        ]

    # ── Task Execution ─────────────────────────────────────
    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "experience")
        delegate = task.get("delegate_to")
        description = task.get("description", "")

        # ── Delegation ────────────────────────────────────
        if delegate and delegate != self.agent_id:
            await self.send_message(
                delegate,
                f"✨ CXO Assignment: {description}",
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
            "user_journey": self._map_user_journey,
            "onboarding": self._design_onboarding,
            "user_research": self._user_research,
            "pmf_tracking": self._track_pmf,
            "feedback_system": self._build_feedback_system,
            "community_experience": self._community_experience,
            "ux_audit": self._ux_audit,
            "support_content": self._create_support_content,
            "persona": self._develop_personas,
            "sentiment": self._monitor_sentiment,
            "discord_management": self._manage_discord_team,
            "cross_team_ux": self._cross_team_ux,
            "nps_design": self._design_nps,
            "retention_strategy": self._retention_strategy,
        }

        handler = handlers.get(task_type)
        if handler:
            return await handler(description)

        # ── Generic UX task ───────────────────────────────
        result = await self.think(
            f"Execute this UX/community task:\n{description}\n\n"
            "Provide specific, actionable output: designs, flows, copy, or research plans."
        )

        if task_type in ("feedback", "community"):
            await self.send_message("ceo", f"UX Insight: {result[:300]}", "feedback")
            await self.send_message("cto", f"UX Improvement Needed: {result[:300]}", "feedback")

        return result

    # ── User Journey Mapping ───────────────────────────────
    async def _map_user_journey(self, description: str) -> str:
        """Map and optimise the complete user journey."""
        current_map = await self.memory.recall("user_journey_map", "ux")

        result = await self.think(
            f"""User journey mapping task: {description}

Current Journey Map: {current_map or 'No map yet — create the complete journey.'}

Product: {settings.product_name} — AI pentesting chatbot
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

Map the FULL user journey with emotional states:

**Stage 1 — Discovery** (How they find us)
- Channels: Google, Reddit, Twitter, HN, word-of-mouth, GitHub Explore
- Emotional state: Curious / Skeptical
- Key question: "Is this legit? Is it better than what I use?"
- Conversion goal: Click → visit GitHub repo
- Friction points & fixes

**Stage 2 — First Impression** (GitHub repo visit)
- What they see first (README hero section)
- Trust signals they look for (stars, activity, badges, license)
- Emotional state: Evaluating / Judging
- Conversion goal: Visit → star or clone
- Time budget: 30 seconds to convince them

**Stage 3 — Installation & Setup**
- Steps from clone to running
- Common failure points
- Emotional state: Impatient / Frustrated if broken
- Conversion goal: Clone → working tool
- Target: Under 3 minutes

**Stage 4 — First Use (Aha Moment)**
- What's the first task they should try?
- When does the "wow, this is useful" moment happen?
- Emotional state: Exploring → Impressed
- Conversion goal: First run → "this is cool"
- Design the ideal first experience

**Stage 5 — Retention & Habit**
- What brings them back?
- Use case patterns (daily tool vs. occasional)
- Emotional state: Comfortable / Reliant
- Conversion goal: One-time → regular user

**Stage 6 — Advocacy**
- What makes them tell others?
- Share triggers (built-in sharing, results screenshot, etc.)
- Emotional state: Proud / Evangelistic
- Conversion goal: User → advocate

For each stage: touchpoints, emotions, friction points, metrics, and specific improvement actions."""
        )

        await self.memory.remember("user_journey_map", result[:800], category="ux")
        await self.broadcast(f"🗺️ User Journey Update: {result[:300]}", channel="ux_update")
        await self.send_message("ceo", f"User Journey Insights: {result[:300]}", "report")
        return result

    # ── Onboarding Design ──────────────────────────────────
    async def _design_onboarding(self, description: str) -> str:
        """Design frictionless onboarding experiences."""
        current_onboarding = await self.memory.recall("onboarding_design", "ux")

        result = await self.think(
            f"""Onboarding design task: {description}

Current Onboarding: {current_onboarding or 'No onboarding designed yet.'}

Design onboarding for TWO surfaces:

**GitHub Onboarding (README → Running)**:
1. Hero section that answers "what is this?" in 5 seconds
2. Quick-start block: exact commands (max 3 steps)
3. Expected output / screenshot description
4. "What to try first" suggestions
5. Troubleshooting for common setup issues
6. Link to Discord for help
- Write the actual README quick-start section

**Discord Onboarding (Join → Value)**:
1. Welcome message copy (DM on join)
2. Channel tour / guide message
3. First action prompt ("Try this in #bot-testing")
4. Role selection (skill level, interests)
5. Welcome channel pinned getting-started guide
6. Auto-role assignment rules
- Write the actual welcome message and guide

**Onboarding Metrics to Track**:
- Time-to-first-value (install → first successful use)
- Onboarding completion rate
- Drop-off points
- Help request rate during onboarding

Write actual copy and content, not just strategy."""
        )

        await self.memory.remember("onboarding_design", result[:600], category="ux")
        await self.send_message("cto", f"Onboarding DX Needs: {result[:300]}", "feedback")
        await self.send_message("discord", f"Discord Onboarding Plan: {result[:400]}", "task_assignment")
        return result

    # ── User Research ──────────────────────────────────────
    async def _user_research(self, description: str) -> str:
        """Design and plan user research activities."""
        prev_research = await self.memory.recall("user_research", "research")

        result = await self.think(
            f"""User research task: {description}

Previous Research: {prev_research or 'No research conducted yet.'}

Design user research activities:

**1. Survey Design** (for Discord/GitHub):
- 5-7 questions, mix of quantitative and qualitative
- Write the actual survey questions
- Distribution plan (where/when/how)
- Expected sample size and timeline

**2. User Interview Script** (for early adopters):
- Intro script
- 8-10 open-ended questions about:
  - Their current pentesting workflow
  - Pain points with existing tools
  - What they'd want from an AI pentesting tool
  - How they discover and evaluate new tools
- Closing and follow-up plan

**3. Competitive UX Analysis**:
- How do competing tools onboard users?
- What UX patterns work in the cybersecurity tool space?
- What can we learn from the best developer tools (not just security)?

**4. Community Listening**:
- What are people saying in r/netsec, r/hacking about AI tools?
- Common questions and pain points
- Unmet needs we can address

**5. Research Synthesis Framework**:
- How to categorise findings (themes, severity, frequency)
- Insight → Action pipeline
- Sharing findings with the team"""
        )

        await self.memory.remember("user_research", result[:600], category="research")
        await self.send_message("ceo", f"Research Findings: {result[:300]}", "report")
        await self.send_message("cmo", f"User Research for Messaging: {result[:300]}", "collaboration")
        return result

    # ── Product-Market Fit ─────────────────────────────────
    async def _track_pmf(self, description: str) -> str:
        """Track and analyse product-market fit signals."""
        pmf_data = await self.memory.recall("pmf_tracking", "metrics")

        result = await self.think(
            f"""Product-market fit tracking: {description}

Current PMF Data: {pmf_data or 'No PMF data yet — define framework.'}

Define and track PMF signals for {settings.product_name}:

**Sean Ellis Test**:
- "How would you feel if you could no longer use {settings.product_name}?"
- Very disappointed / Somewhat disappointed / Not disappointed
- Target: >40% "very disappointed" = PMF achieved

**Leading Indicators** (track weekly):
1. Organic star velocity (stars/week without promotion)
2. Organic Discord joins (joins without active campaign)
3. GitHub issue quality (feature requests vs bugs — more features = good signal)
4. Return usage (users who come back after first try)
5. Word-of-mouth mentions (social, Reddit, forums)

**Lagging Indicators**:
1. 7-day retention rate
2. Net Promoter Score
3. Contributor growth rate
4. Fork-to-star ratio (forks = serious usage)

**PMF Dashboard**:
- Current estimates for each metric
- Trend direction (↑ / → / ↓)
- Target thresholds
- Actions to improve the weakest signal

**PMF Experiments**:
- 3 experiments to test PMF hypotheses
- Each with: hypothesis, method, success criteria, timeline"""
        )

        await self.memory.remember("pmf_tracking", result[:600], category="metrics")
        await self.send_message("ceo", f"📈 PMF Update: {result[:300]}", "report")
        return result

    # ── Feedback System ────────────────────────────────────
    async def _build_feedback_system(self, description: str) -> str:
        """Design and maintain feedback collection and processing systems."""
        result = await self.think(
            f"""Feedback system task: {description}

Build a comprehensive feedback collection system:

**1. GitHub Feedback Channels**:
- Issue templates for: bug report, feature request, UX feedback, question
- Discussion board categories
- Reaction-based feature voting
- Template copy (write the actual templates)

**2. Discord Feedback Channels**:
- #feedback channel rules and pinned message
- #feature-requests with voting reactions
- #bug-reports with structured format
- Feedback bot commands (/suggest, /bug, /vote)
- Write the actual channel descriptions and pinned messages

**3. In-Product Feedback** (future):
- When to prompt for feedback (after first success, after error, weekly)
- Feedback widget design
- Crash/error auto-reporting

**4. Feedback Processing Pipeline**:
- Triage: How to categorise incoming feedback
- Prioritisation: Impact × Frequency matrix
- Routing: Which team handles what
- Response SLA: First response within 24h
- Closing the loop: Tell users when their feedback is implemented

**5. Feedback Synthesis**:
- Weekly summary format
- Top themes and trends
- Insight → Action items with owners

Write actual templates and copy."""
        )

        await self.send_message("cto", f"Feedback Templates for GitHub: {result[:300]}", "feedback")
        await self.send_message("discord", f"Discord Feedback Setup: {result[:400]}", "task_assignment")
        await self.memory.remember("feedback_system", result[:600], category="ux")
        return result

    # ── Community Experience ────────────────────────────────
    async def _community_experience(self, description: str) -> str:
        """Design and improve the overall community experience."""
        discord_status = await self._collect_discord_status()

        result = await self.think(
            f"""Community experience task: {description}

Discord Team Status: {discord_status}

Design the ideal community experience:

**Discord Server Architecture**:
- Category and channel structure (name, purpose, emoji)
- Role hierarchy (newcomer → member → contributor → moderator → team)
- Permission matrix
- Auto-moderation rules
- Write actual channel descriptions

**Community Rituals** (recurring events):
- Weekly: Challenge of the week, tool tip Tuesday
- Biweekly: Community call / AMA
- Monthly: CTF night, contributor spotlight
- Quarterly: Roadmap review, community survey
- Event format and copy for each

**Community Health Metrics**:
- Messages per day
- Active members (DAU/WAU/MAU)
- New member retention (join → still active after 7 days)
- Help-to-resolution time
- Engagement depth (lurker → poster → helper)

**Toxicity Prevention**:
- Code of conduct (write it)
- Moderation guidelines
- Escalation process
- Warning/ban policy

**Community Gamification**:
- XP/level system concept
- Achievement badges
- Leaderboard mechanics
- Reward ideas (Discord roles, shoutouts, swag)"""
        )

        await self.send_message("discord", f"🌟 Community Experience Plan: {result[:400]}", "task_assignment")
        await self.memory.remember("community_experience", result[:600], category="community")
        return result

    # ── UX Audit ───────────────────────────────────────────
    async def _ux_audit(self, description: str) -> str:
        """Audit the product and community UX for friction and issues."""
        prev_audit = await self.memory.recall("ux_audit", "ux")

        result = await self.think(
            f"""UX audit task: {description}

Previous Audit: {prev_audit or 'No previous audit.'}
Product: {settings.product_name}

Conduct a UX audit across all touchpoints:

**1. GitHub Repo UX**:
- README readability (scan time, clarity, structure)
- Navigation (can users find what they need?)
- Issue/PR experience
- Documentation completeness

**2. Installation UX**:
- Dependency pain points
- Error messages (clear? helpful? actionable?)
- Platform compatibility
- Environment setup friction

**3. CLI/Product UX** (if applicable):
- First-run experience
- Command discoverability
- Output formatting and readability
- Error handling and recovery suggestions
- Progress feedback for long operations

**4. Discord UX**:
- Join-to-value time
- Channel discoverability
- Bot interaction quality
- Help availability

**5. Documentation UX**:
- Findability (can users find answers?)
- Accuracy (is it up to date?)
- Completeness (are there gaps?)
- Readability (is it accessible to beginners?)

For EACH issue found:
- Severity: 🔴 Critical / 🟡 Major / 🟢 Minor
- Screenshot/description of the problem
- Recommended fix
- Effort to fix (S/M/L)
- Impact on user experience"""
        )

        await self.memory.remember("ux_audit", result[:600], category="ux")
        await self.send_message("cto", f"🔍 UX Audit Findings: {result[:400]}", "feedback")
        await self.send_message("ceo", f"UX Audit Summary: {result[:300]}", "report")
        return result

    # ── Support Content ────────────────────────────────────
    async def _create_support_content(self, description: str) -> str:
        """Create FAQ, troubleshooting guides, and help content."""
        result = await self.think(
            f"""Support content task: {description}

Product: {settings.product_name} — AI pentesting chatbot

Create ready-to-publish support content:

**FAQ (write 10-15 questions and answers)**:
- What is {settings.product_name}?
- Is it free?
- What can it do? / What CAN'T it do?
- Is it legal to use?
- How does it compare to [competitor]?
- What models does it support?
- How do I install it?
- How do I get help?
- Can I contribute?
- Is my data safe? / Does it phone home?
- What's the roadmap?

**Troubleshooting Guide**:
- Common installation errors and fixes
- API key issues
- Docker problems
- Platform-specific gotchas

**Quick-Start Tutorial** (step by step):
- Prerequisites
- Installation
- Configuration
- First scan/test
- Understanding results
- Next steps

Write the ACTUAL content, ready to paste into docs or Discord."""
        )

        await self.send_message("cto", f"Support Docs for Review: {result[:300]}", "content")
        await self.send_message("discord", f"FAQ for Discord: {result[:400]}", "task_assignment")
        await self.memory.remember("support_content", result[:600], category="content")
        return result

    # ── Persona Development ────────────────────────────────
    async def _develop_personas(self, description: str) -> str:
        """Create and maintain detailed user personas."""
        existing_personas = await self.memory.recall("user_personas", "research")

        result = await self.think(
            f"""User persona development: {description}

Existing Personas: {existing_personas or 'No personas yet — create initial set.'}

Create 4 detailed personas for {settings.product_name}:

**Persona Template** (for each):
- **Name & Photo Description** (fictional)
- **Role**: Job title and company type
- **Demographics**: Age, experience level, location
- **Goals**: What they want to achieve
- **Frustrations**: Current pain points
- **Tools They Use**: Current toolkit
- **Day in Their Life**: Typical workflow
- **Jobs-to-be-Done**: Functional, emotional, social jobs
- **How They'd Use {settings.product_name}**: Specific use cases
- **What Would Make Them Star the Repo**: Trigger moment
- **What Would Make Them Join Discord**: Community value
- **Objections/Concerns**: Why they might NOT use it
- **Quote** (fictional): A line that captures their mindset

Suggested personas:
1. Professional Pentester — bug bounty hunter, works solo
2. Security Student — learning, wants hands-on tools
3. CTF Player — competitive, wants edge in challenges
4. Security Engineer — enterprise, evaluates tools for team"""
        )

        await self.memory.remember("user_personas", result[:800], category="research")
        await self.send_message("cmo", f"User Personas: {result[:400]}", "collaboration")
        await self.send_message("ceo", f"Persona Update: {result[:300]}", "report")
        return result

    # ── Sentiment Monitoring ───────────────────────────────
    async def _monitor_sentiment(self, description: str) -> str:
        """Track community sentiment and identify concerns early."""
        prev_sentiment = await self.memory.recall("sentiment_tracking", "metrics")

        result = await self.think(
            f"""Sentiment monitoring task: {description}

Previous Sentiment Data: {prev_sentiment or 'No sentiment data yet.'}

Design and execute sentiment monitoring:

**1. Sentiment Sources**:
- GitHub issues and comments tone
- Discord message sentiment
- Social media mentions
- Reddit discussion tone

**2. Sentiment Categories**:
- 😀 Positive: Praise, excitement, recommendations
- 😐 Neutral: Questions, information seeking
- 😟 Negative: Complaints, frustration, bugs
- 🚨 Critical: Anger, threats to leave, public complaints

**3. Current Sentiment Assessment**:
- Overall mood: [estimate based on available data]
- Top positive signals
- Top concerns/complaints
- Emerging trends

**4. Early Warning Signs** to watch for:
- Increase in "doesn't work" messages
- Drop in engagement
- Competitor mentions ("I switched to X")
- Silence (no feedback is not good feedback)

**5. Sentiment Response Playbook**:
- How to respond to praise (amplify, screenshot, repost)
- How to respond to frustration (acknowledge, fix, follow up)
- How to respond to criticism (listen, don't be defensive, act)
- Escalation triggers (when to involve CEO/CTO)"""
        )

        await self.memory.remember("sentiment_tracking", result[:600], category="metrics")
        await self.send_message("ceo", f"😊 Sentiment Report: {result[:300]}", "report")
        return result

    # ── Discord Team Management ────────────────────────────
    async def _manage_discord_team(self, description: str) -> str:
        """Direct and review the Discord team agent."""
        discord_tasks = await state_manager.get_agent_tasks("discord", limit=10)
        discord_msgs = await self._get_team_messages("discord")

        result = await self.think(
            f"""Discord team management: {description}

Discord Team Tasks:
{json.dumps(discord_tasks, indent=2) if discord_tasks else 'No tasks logged.'}

Messages from Discord Team:
{discord_msgs}

Review and direct:

1. **Performance Assessment**: Rate their recent work (A-F)
2. **Community Health Check**: Is Discord growing, engaged, healthy?
3. **Content Quality**: Are community messages, events, and bots good?
4. **New Directives**: 3-5 specific tasks for next cycle
5. **Process Improvements**: Any workflow changes needed?"""
        )

        directives = await self.think_json(
            f"Create 3 specific tasks for the Discord team. "
            f"Return a JSON array with 'description' and 'priority' keys.\n\n{result}",
        )
        if isinstance(directives, list):
            for d in directives[:3]:
                if isinstance(d, dict) and "description" in d:
                    await self.send_message(
                        "discord",
                        f"✨ CXO Task: {d['description']}",
                        channel="task_assignment",
                    )

        return result

    # ── Cross-Team UX Advocacy ─────────────────────────────
    async def _cross_team_ux(self, description: str) -> str:
        """Push UX improvements across all teams."""
        journey = await self.memory.recall("user_journey_map", "ux")
        audit = await self.memory.recall("ux_audit", "ux")

        result = await self.think(
            f"""Cross-team UX advocacy: {description}

User Journey: {journey[:300] if journey else 'Not mapped yet.'}
UX Audit: {audit[:300] if audit else 'Not conducted yet.'}

Identify UX improvements each team should make:

**For CTO/Engineering**:
- Error message improvements
- CLI output formatting
- Setup script usability
- API ergonomics

**For CMO/Marketing**:
- Messaging accuracy (does marketing match reality?)
- Content accessibility
- Landing page UX
- Social proof placement

**For Sales**:
- Demo script improvements
- User testimonial collection
- Case study development

**For Discord**:
- Channel navigation
- Bot UX
- Event experience
- Onboarding flow

For each: specific issue, proposed fix, expected impact on user satisfaction."""
        )

        # Send targeted UX feedback to each team
        await self.send_message("cto", f"🎯 UX Improvements for Engineering: {result[:300]}", "feedback")
        await self.send_message("cmo", f"🎯 UX Check on Marketing: {result[:300]}", "feedback")
        await self.send_message("discord", f"🎯 Discord UX Tasks: {result[:300]}", "feedback")
        return result

    # ── NPS Design ─────────────────────────────────────────
    async def _design_nps(self, description: str) -> str:
        """Design the Net Promoter Score collection and tracking system."""
        result = await self.think(
            f"""NPS system design: {description}

Design a complete NPS program for {settings.product_name}:

**1. NPS Survey**:
- Primary question: "How likely are you to recommend {settings.product_name} to a friend or colleague? (0-10)"
- Follow-up for Promoters (9-10): "What do you love most?"
- Follow-up for Passives (7-8): "What would make you rate us higher?"
- Follow-up for Detractors (0-6): "What's your biggest frustration?"

**2. Collection Channels**:
- Discord bot command (/nps)
- GitHub Discussion periodic post
- In-product prompt (after 5 uses)
- Email survey (if email collected)

**3. Cadence**:
- Monthly NPS survey
- Quarterly deep-dive analysis
- Post-release pulse surveys

**4. Response Playbook**:
- Promoters: Ask for GitHub star, Discord invite, testimonial
- Passives: Ask for specific feedback, send improvement update
- Detractors: Personal outreach within 24h, fix their top issue

**5. NPS Dashboard Metrics**:
- Overall NPS score
- Trend over time
- NPS by persona/segment
- Individual response tracking

Write actual survey copy and bot command responses."""
        )

        await self.memory.remember("nps_tracking", result[:600], category="metrics")
        await self.send_message("discord", f"NPS Bot Setup: {result[:300]}", "task_assignment")
        return result

    # ── Retention Strategy ─────────────────────────────────
    async def _retention_strategy(self, description: str) -> str:
        """Design strategies to retain and re-engage users."""
        pmf = await self.memory.recall("pmf_tracking", "metrics")

        result = await self.think(
            f"""Retention strategy task: {description}

PMF Data: {pmf or 'No data yet.'}

Design a retention strategy for {settings.product_name}:

**1. Activation Triggers** (get users to "aha moment"):
- Define the aha moment precisely
- Steps to reach it faster
- Guided first experience

**2. Engagement Hooks**:
- Daily/weekly reasons to return
- New content/challenges/updates cadence
- Discord notifications worth clicking

**3. Re-engagement Campaigns**:
- Inactive user detection (no activity > 7 days)
- Win-back messages (Discord, GitHub, email)
- "What's new" summaries
- Personal outreach for high-value users

**4. Habit Loop Design**:
- Trigger → Action → Reward → Investment
- What's the natural trigger? (new pentest engagement)
- What's the reward? (faster, better results)
- What's the investment? (custom configs, saved results)

**5. Churn Prevention**:
- Warning signs of churn
- Intervention points
- Exit survey design

Provide copy for re-engagement messages and specific mechanics."""
        )

        await self.memory.remember("retention_strategy", result[:600], category="ux")
        await self.send_message("ceo", f"Retention Strategy: {result[:300]}", "report")
        await self.send_message("cmo", f"Re-engagement Campaign Ideas: {result[:300]}", "collaboration")
        return result

    # ── Intelligence Gathering ─────────────────────────────
    async def _collect_discord_status(self) -> str:
        """Gather status from the Discord team."""
        tasks = await state_manager.get_agent_tasks("discord", limit=5)
        lines = []
        if tasks:
            lines.append("**Discord Team:**")
            for t in tasks:
                lines.append(f"  - {t.get('task_type','?')}: {t.get('description','')[:80]} [{t.get('status','')}]")
        else:
            lines.append("Discord Team: No tasks logged yet.")
        return "\n".join(lines)

    async def _get_inbox_summary(self) -> str:
        """Get incoming messages."""
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
        """CXO generates a user-experience focused report."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]

        journey = await self.memory.recall("user_journey_map", "ux")
        nps = await self.memory.recall("nps_tracking", "metrics")
        sentiment = await self.memory.recall("sentiment_tracking", "metrics")

        report = await self.think(
            f"""Generate the CXO daily experience report.

## Your Tasks Today
{json.dumps(today_tasks, indent=2) if today_tasks else 'No CXO tasks today.'}

## User Journey Status
{journey[:200] if journey else 'Not mapped yet.'}

## NPS Data
{nps[:200] if nps else 'Not tracked yet.'}

## Community Sentiment
{sentiment[:200] if sentiment else 'Not monitored yet.'}

Write a concise experience report:
1. User experience improvements made today
2. Community health and sentiment
3. Onboarding status
4. Feedback highlights (praise and complaints)
5. Tomorrow's UX priorities (top 3)
6. Experience health: 🟢 green / 🟡 yellow / 🔴 red

Under 250 words. Focus on the user."""
        )

        await state_manager.save_daily_report(self.agent_id, report)
        return f"**CXO Experience Report**\n{report}"
