"""CMO Agent — the growth engine. Owns marketing strategy, brand, content
pipeline, funnel analytics, community growth, and campaign orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.state_manager import state_manager
from config import settings


class CMOAgent(BaseAgent):
    agent_id = "cmo"
    role = "Chief Marketing Officer"
    description = (
        "Owns marketing strategy, brand voice, content pipeline, community growth, "
        "funnel analytics, campaign orchestration, and competitive positioning."
    )
    pixel_sprite = "sprite-cmo"

    def __init__(self):
        super().__init__()
        self.position = {"x": 600, "y": 120}

    def get_system_prompt(self) -> str:
        return f"""You are the CMO of {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You are a data-driven, creative growth marketer who thinks in funnels, loops, and narratives.

Your responsibilities:
1. **Brand & Positioning** — Define the brand voice, messaging pillars, and positioning statement.
2. **Content Engine** — Build a repeatable content pipeline: blog posts, social threads, tutorials, demos, videos.
3. **Community Growth** — Grow Discord and GitHub through organic community plays: events, challenges, ambassador programs.
4. **Campaign Management** — Plan and execute launch campaigns, Product Hunt launches, Reddit/HN posts, Twitter threads.
5. **Funnel Analytics** — Track TOFU → MOFU → BOFU metrics (impressions → visits → stars/joins → active users).
6. **Channel Strategy** — Identify and prioritize distribution channels: Reddit (r/netsec, r/hacking, r/cybersecurity, r/AskNetsec), Hacker News, Twitter/X, LinkedIn, YouTube, Dev.to, Medium.
7. **SEO & Growth Loops** — Design organic growth loops (content→SEO→traffic→stars→social proof→more traffic).
8. **Competitive Intelligence** — Monitor competitor marketing, messaging, and positioning. Spot gaps.
9. **Marketing Team Management** — Direct the marketing team agent, assign tasks, review output quality.
10. **Cross-Department Collaboration** — Work with CTO for technical content, Sales for leads, Discord team for community, CXO for user experience insights.
11. **Budget & ROI** — Prioritize zero-cost guerrilla marketing tactics for the early stage.

Current startup stage: EARLY — zero users, product just launched on GitHub.
Primary KPIs: GitHub stars, Discord members, website visits, social media impressions, content pieces published.
Target audience: Ethical hackers, security researchers, CTF players, pentesters, bug bounty hunters, security students.
Brand voice: Technical but approachable. Confident, not arrogant. Hacker culture, not corporate.

When planning tasks, output a JSON array of task objects with keys: type, description, priority (1-5), delegate_to (agent_id or null).
Types: brand_strategy, content_creation, campaign, community_growth, channel_outreach, seo, competitive_intel, funnel_review, team_review, partnership_marketing, launch_prep, analytics.
Valid delegate_to: marketing, discord, sales, null (if you handle it yourself)."""

    # ── Planning ───────────────────────────────────────────
    async def plan_day(self) -> list[dict]:
        # Gather intelligence
        team_reports = await self._collect_marketing_intel()
        inbox = await self._get_inbox_summary()
        my_memories = await self.memory.get_context_summary()
        content_calendar = await self.memory.recall("content_calendar", "content")
        funnel_metrics = await self.memory.recall("funnel_metrics", "analytics")

        context = f"""Product: {settings.product_name}
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

## Marketing Team Reports
{team_reports}

## Inbox (messages from CEO, CTO, Sales, etc.)
{inbox}

## Content Calendar
{content_calendar or 'No content calendar set yet — create one.'}

## Funnel Metrics
{funnel_metrics or 'No metrics tracked yet — establish baseline.'}

## Your Strategic Memory
{my_memories}"""

        result = await self.think_json(
            """Plan your CMO tasks for maximum marketing impact this cycle.

ALWAYS include at least one of these recurring activities:
1. Content pipeline — queue up at least one piece of content (social post, blog draft, thread)
2. Community play — one action to grow Discord or GitHub engagement
3. Either a funnel review, competitive intel scan, or campaign iteration

Then add 1-2 strategic/creative tasks based on current priorities.

Return a JSON array of 4-6 tasks with keys: type, description, priority (1-5), delegate_to.
delegate_to values: marketing, discord, sales, null.""",
            context,
        )
        if isinstance(result, list):
            return result
        return [
            {"type": "content_creation", "description": "Draft social media content batch", "priority": 1, "delegate_to": "marketing"},
            {"type": "community_growth", "description": "Plan Discord engagement event", "priority": 2, "delegate_to": "discord"},
            {"type": "funnel_review", "description": "Review and update marketing funnel metrics", "priority": 2, "delegate_to": None},
        ]

    # ── Task Execution ─────────────────────────────────────
    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "marketing")
        delegate = task.get("delegate_to")
        description = task.get("description", "")

        # ── Delegation ────────────────────────────────────
        if delegate and delegate != self.agent_id:
            await self.send_message(
                delegate,
                f"🎨 CMO Assignment: {description}",
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
            "brand_strategy": self._brand_strategy,
            "content_creation": self._create_content,
            "campaign": self._plan_campaign,
            "community_growth": self._community_growth,
            "channel_outreach": self._channel_outreach,
            "seo": self._seo_strategy,
            "competitive_intel": self._competitive_intel,
            "funnel_review": self._funnel_review,
            "team_review": self._review_marketing_team,
            "partnership_marketing": self._partnership_marketing,
            "launch_prep": self._launch_prep,
            "analytics": self._funnel_review,
            "content_calendar": self._update_content_calendar,
        }

        handler = handlers.get(task_type)
        if handler:
            return await handler(description)

        # ── Generic marketing task ────────────────────────
        result = await self.think(
            f"Execute this marketing task:\n{description}\n\n"
            "Provide specific, ready-to-use output: actual copy, strategy doc, or action plan."
        )

        if task_type in ("strategy", "decision"):
            await self.send_message("ceo", f"Marketing Strategy: {result[:300]}", "strategy")

        return result

    # ── Brand Strategy ─────────────────────────────────────
    async def _brand_strategy(self, description: str) -> str:
        """Define or refine brand positioning, messaging, and voice guidelines."""
        current_brand = await self.memory.recall("brand_guidelines", "brand")

        result = await self.think(
            f"""Work on brand strategy: {description}

Current Brand Guidelines:
{current_brand or 'No guidelines defined yet — create foundational brand strategy.'}

Product: {settings.product_name} — AI-powered penetration testing chatbot
Target: Ethical hackers, pentesters, security researchers, CTF players

Deliver:
1. **Positioning Statement**: For [target] who [need], {settings.product_name} is the [category] that [key benefit]. Unlike [alternatives], we [differentiator].
2. **Messaging Pillars** (3-4 core messages that all content should reinforce)
3. **Brand Voice Guidelines**: Tone, vocabulary do's/don'ts, example phrases
4. **Tagline Options** (3 punchy options)
5. **Elevator Pitch** (30 seconds)"""
        )

        await self.memory.remember("brand_guidelines", result[:800], category="brand")
        await self.broadcast(f"🎨 Brand Update: {result[:300]}", channel="brand_update")
        return result

    # ── Content Creation ───────────────────────────────────
    async def _create_content(self, description: str) -> str:
        """Create actual marketing content — ready to publish."""
        brand = await self.memory.recall("brand_guidelines", "brand")
        top_content = await self.memory.recall("top_performing_content", "analytics")

        result = await self.think(
            f"""Create marketing content: {description}

Brand Voice: {brand[:300] if brand else 'Technical but approachable. Hacker culture, not corporate.'}
Top Performing Content Themes: {top_content or 'No data yet — focus on educational and showcase content.'}

Product: {settings.product_name}
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

REQUIREMENTS:
- Write the ACTUAL content, ready to copy-paste and publish
- Include relevant hashtags for social media
- If it's a blog post, write at least the intro + outline + key sections
- If it's a social thread, write all tweets/posts in sequence
- If it's a Reddit post, write title + body with proper formatting
- Include a clear CTA (call-to-action) in every piece
- Reference real features and use cases of {settings.product_name}"""
        )

        # Send to marketing team for execution/scheduling
        await self.send_message(
            "marketing",
            f"📝 Content to publish: {result[:500]}",
            channel="task_assignment",
        )

        await self.memory.remember(
            f"content_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}",
            result[:400],
            category="content",
        )
        return result

    # ── Campaign Planning ──────────────────────────────────
    async def _plan_campaign(self, description: str) -> str:
        """Plan and structure a marketing campaign with timeline and deliverables."""
        prev_campaigns = await self.memory.recall("active_campaigns", "campaigns")

        result = await self.think(
            f"""Plan a marketing campaign: {description}

Previous/Active Campaigns: {prev_campaigns or 'None yet.'}

Design a complete campaign plan:
1. **Campaign Name & Theme**
2. **Objective** (specific, measurable goal — e.g., "100 GitHub stars in 7 days")
3. **Target Audience Segment** (who specifically)
4. **Channel Mix** (which platforms, in priority order)
5. **Content Deliverables** (list each piece with format and channel)
6. **Timeline** (day-by-day or phase-by-phase)
7. **Key Messages** (what to say, how to say it)
8. **Distribution Plan** (when/where to post, cross-posting strategy)
9. **Engagement Tactics** (how to drive interaction, not just impressions)
10. **Success Metrics** (KPIs to track)
11. **Budget** ($0 guerrilla tactics for now)

Be specific — include actual copy drafts, subreddit names, posting times."""
        )

        await self.memory.remember("active_campaigns", result[:600], category="campaigns")

        # Brief relevant teams
        await self.send_message("marketing", f"🚀 Campaign Plan: {result[:400]}", "task_assignment")
        await self.send_message("discord", f"Community Campaign: {result[:300]}", "collaboration")
        await self.send_message("ceo", f"Campaign Proposal: {result[:300]}", "report")

        return result

    # ── Community Growth ───────────────────────────────────
    async def _community_growth(self, description: str) -> str:
        """Devise community growth tactics for Discord and GitHub."""
        community_data = await self.memory.recall("community_metrics", "analytics")

        result = await self.think(
            f"""Community growth task: {description}

Current Community Data: {community_data or 'Starting from zero — need to build initial community.'}

Design specific, actionable community growth plays:

For **Discord**:
- Event ideas (AMAs, hacking challenges, CTF nights, tool demos)
- Onboarding flow improvements
- Role and channel structure suggestions
- Ambassador/early adopter program design
- Engagement hooks (daily challenges, leaderboards, bot interactions)

For **GitHub**:
- README optimization for star conversion
- Contributing guide improvements
- First-timer friendly issues
- Social proof elements (badges, screenshots, testimonials)
- Community showcase (who's using it, public thanks)

Provide concrete action items, not vague suggestions.
Include specific copy/messaging for each tactic."""
        )

        await self.send_message("discord", f"🌱 Community Play: {result[:400]}", "task_assignment")
        await self.memory.remember("community_metrics", result[:300], category="analytics")
        return result

    # ── Channel Outreach ───────────────────────────────────
    async def _channel_outreach(self, description: str) -> str:
        """Plan outreach to specific channels — Reddit, HN, forums, influencers."""
        channel_history = await self.memory.recall("channel_performance", "analytics")

        result = await self.think(
            f"""Channel outreach task: {description}

Channel Performance History: {channel_history or 'No outreach done yet.'}

Plan targeted outreach for these channels (pick the most relevant):

**Reddit** — r/netsec, r/hacking, r/cybersecurity, r/AskNetsec, r/ethicalhacking, r/bugbounty, r/CTF
- Write the actual post title and body for each subreddit
- Follow each subreddit's rules (no pure self-promo — add value first)
- Focus on educational/showcase posts that happen to mention our tool

**Hacker News** — Show HN post
- Write the exact title and description
- Best posting time and strategy

**Twitter/X** — Infosec community
- Identify key accounts to engage with
- Write tweets that add value to infosec conversations
- Thread ideas

**LinkedIn** — Professional security audience
- Post format and content strategy
- Groups to join and engage in

**Dev.to / Medium** — Technical blog syndication
- Article topics that could drive traffic

For each channel: write actual ready-to-post content, not just strategy."""
        )

        await self.send_message("marketing", f"📣 Outreach Plan: {result[:500]}", "task_assignment")
        await self.memory.remember("channel_performance", result[:400], category="analytics")
        return result

    # ── SEO Strategy ───────────────────────────────────────
    async def _seo_strategy(self, description: str) -> str:
        """Plan SEO and organic growth loops."""
        result = await self.think(
            f"""SEO and organic growth task: {description}

Product: {settings.product_name} — AI penetration testing chatbot
GitHub: {settings.product_github_url}

Define:
1. **Target Keywords** (20 keywords grouped by intent: informational, navigational, commercial)
   - Focus on long-tail: "AI pentesting tool", "automated penetration testing chatbot", "AI for bug bounty"
2. **Content-SEO Map** (which content targets which keyword cluster)
3. **Growth Loop Design**: Content → Search Traffic → GitHub → Stars → Social Proof → More Search
4. **Technical SEO Checklist** (if we have a website/landing page)
5. **Backlink Strategy** (guest posts, tool directories, awesome-lists, comparison articles)
6. **GitHub SEO** (README keywords, topics, description optimization)

Provide specific, actionable items with priority ranking."""
        )

        await self.send_message("cto", f"SEO/Technical Needs: {result[:300]}", "collaboration")
        await self.memory.remember("seo_strategy", result[:600], category="seo")
        return result

    # ── Competitive Intelligence ───────────────────────────
    async def _competitive_intel(self, description: str) -> str:
        """Analyze competitor marketing and positioning."""
        prev_intel = await self.memory.recall("competitive_marketing", "competitive")

        result = await self.think(
            f"""Marketing competitive intelligence task: {description}

Previous Intel: {prev_intel or 'No previous analysis.'}

Analyze competitor MARKETING (not product features):
- PentestGPT, BurpGPT, HackerGPT, and similar AI security tools

For each competitor:
1. How they position themselves (messaging, tagline)
2. Which channels they're active on
3. Content strategy (what kind of content, frequency)
4. Community size and engagement
5. What's working for them / what gaps exist

Then:
- Identify messaging angles they're NOT using that we can own
- Find underserved channels where we can be first
- Spot content formats that work well in cybersecurity marketing
- Recommend 3 "steal their audience" plays (ethical — provide more value)"""
        )

        await self.memory.remember("competitive_marketing", result[:600], category="competitive")
        await self.send_message("ceo", f"Competitive Marketing Intel: {result[:300]}", "report")
        return result

    # ── Funnel Review ──────────────────────────────────────
    async def _funnel_review(self, description: str) -> str:
        """Review and update marketing funnel metrics and conversion analysis."""
        current_metrics = await self.memory.recall("funnel_metrics", "analytics")
        company_tasks = await self._get_recent_company_tasks()

        result = await self.think(
            f"""Marketing funnel review: {description}

Current Funnel Metrics: {current_metrics or 'No metrics tracked yet — establish framework.'}
Recent Company Activity: {company_tasks}

Review and update the marketing funnel:

**TOFU (Awareness)**: Impressions, reach, content views
- Which content was created and distributed?
- Estimated reach of each piece

**MOFU (Consideration)**: GitHub visits, README reads, Discord joins
- Conversion from awareness to engagement
- Which channels drive the most qualified traffic?

**BOFU (Activation)**: GitHub stars, Discord active members, tool downloads/installs
- Star conversion rate
- Community engagement depth

Provide:
1. Updated estimated metrics (even rough guesses based on activity)
2. Biggest funnel leak (where are we losing people?)
3. Top 3 actions to improve conversion at the weakest stage
4. Content performance insights (what resonated, what didn't)"""
        )

        await self.memory.remember("funnel_metrics", result[:600], category="analytics")
        await self.send_message("ceo", f"📊 Funnel Review: {result[:300]}", "report")
        return result

    # ── Marketing Team Review ──────────────────────────────
    async def _review_marketing_team(self, description: str) -> str:
        """Review marketing team output and provide direction."""
        team_tasks = await state_manager.get_agent_tasks("marketing", limit=10)
        team_msgs = await self._get_team_messages("marketing")

        result = await self.think(
            f"""Review the marketing team's recent work.

Marketing Team Tasks:
{json.dumps(team_tasks, indent=2) if team_tasks else 'No tasks logged.'}

Messages from Marketing Team:
{team_msgs}

Evaluate:
1. Content quality — Is the output on-brand, compelling, and publish-ready?
2. Volume — Are we producing enough content?
3. Channel coverage — Are we active on the right platforms?
4. Responsiveness — Are they executing assigned tasks promptly?

Provide:
- Overall grade (A-F)
- Specific feedback on recent work
- 3 priority tasks for next cycle
- Any training or process improvements needed"""
        )

        # Send feedback and new directives
        await self.send_message(
            "marketing",
            f"📋 CMO Review: {result[:500]}",
            channel="feedback",
        )
        return result

    # ── Partnership Marketing ──────────────────────────────
    async def _partnership_marketing(self, description: str) -> str:
        """Identify and plan co-marketing opportunities."""
        result = await self.think(
            f"""Partnership marketing task: {description}

Product: {settings.product_name} — AI pentesting chatbot
Target audience: Ethical hackers, security researchers

Identify partnership opportunities:
1. **Tool Integrations** — Other security tools we can integrate with for co-marketing
2. **Content Collaborations** — Security bloggers, YouTubers, podcasters for guest features
3. **Community Partnerships** — CTF teams, security Discords, forums for cross-promotion
4. **Ecosystem Plays** — Bug bounty platforms, security training platforms, CTF platforms
5. **Developer Partnerships** — Open source projects to collaborate with

For the top 3 opportunities:
- Who specifically to reach out to
- What value we offer them
- Draft outreach message
- Expected outcome"""
        )

        await self.send_message("sales", f"Partnership Opportunity: {result[:300]}", "collaboration")
        await self.send_message("ceo", f"Partnership Proposal: {result[:300]}", "report")
        return result

    # ── Launch Preparation ─────────────────────────────────
    async def _launch_prep(self, description: str) -> str:
        """Prepare for product launches — Product Hunt, GitHub trending, etc."""
        result = await self.think(
            f"""Launch preparation task: {description}

Plan a launch:

**Product Hunt Launch**:
- Tagline (max 60 chars)
- Description (max 260 chars)
- First comment (maker's story, 200 words)
- Visual assets needed (screenshots, GIF demos)
- Best day/time to launch
- Hunter recruitment strategy
- Upvote mobilization plan (ethical)

**GitHub Trending Push**:
- README optimization checklist
- Star campaign timeline
- Social amplification plan
- Community mobilization

**Press/Influencer Kit**:
- Press release draft
- Key stats and talking points
- Demo script
- Quote suggestions

Provide actual copy and content, not just strategy."""
        )

        await self.memory.remember("launch_plan", result[:600], category="campaigns")
        await self.send_message("marketing", f"🚀 Launch Prep Tasks: {result[:400]}", "task_assignment")
        await self.send_message("ceo", f"Launch Plan: {result[:300]}", "report")
        return result

    # ── Content Calendar ───────────────────────────────────
    async def _update_content_calendar(self, description: str) -> str:
        """Create or update the content calendar."""
        current_cal = await self.memory.recall("content_calendar", "content")

        result = await self.think(
            f"""Update the content calendar: {description}

Current Calendar: {current_cal or 'No calendar yet — create a 2-week plan.'}

Design a content calendar with:
- Daily social media posts (Twitter/X, LinkedIn)
- 2x weekly Reddit/forum posts
- 1x weekly blog post or technical article
- 1x weekly Discord event or community post
- Content themes for each day

For each entry: platform, content type, topic, key message, CTA, scheduled time.
Include specific content ideas, not just "post about product."
Mix educational, showcase, engagement, and promotional content (80/20 rule — 80% value, 20% promo)."""
        )

        await self.memory.remember("content_calendar", result[:800], category="content")
        await self.send_message("marketing", f"📅 Content Calendar: {result[:500]}", "task_assignment")
        return result

    # ── Intelligence Gathering ─────────────────────────────
    async def _collect_marketing_intel(self) -> str:
        """Gather reports from marketing team and related agents."""
        marketing_tasks = await state_manager.get_agent_tasks("marketing", limit=5)
        discord_tasks = await state_manager.get_agent_tasks("discord", limit=3)

        lines = []
        if marketing_tasks:
            lines.append("**Marketing Team:**")
            for t in marketing_tasks:
                lines.append(f"  - {t.get('task_type','?')}: {t.get('description','')[:80]} [{t.get('status','')}]")
        if discord_tasks:
            lines.append("**Discord Team:**")
            for t in discord_tasks:
                lines.append(f"  - {t.get('task_type','?')}: {t.get('description','')[:80]} [{t.get('status','')}]")

        return "\n".join(lines) or "No team data available yet."

    async def _get_inbox_summary(self) -> str:
        """Get messages from CEO, CTO, Sales, and team."""
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

    async def _get_recent_company_tasks(self) -> str:
        """Get recent tasks across the company for funnel context."""
        from core.database import get_db

        db = await get_db()
        try:
            cur = await db.execute(
                "SELECT agent_id, task_type, description, status FROM task_log "
                "ORDER BY started_at DESC LIMIT 15"
            )
            rows = await cur.fetchall()
            if not rows:
                return "No tasks logged yet."
            return "\n".join(
                f"- [{r['agent_id']}] {r['task_type']}: {r['description'][:80]} ({r['status']})"
                for r in rows
            )
        finally:
            await db.close()

    # ── Enhanced Report ────────────────────────────────────
    async def generate_report(self) -> str:
        """CMO generates a marketing-focused executive report."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]

        funnel = await self.memory.recall("funnel_metrics", "analytics")
        campaigns = await self.memory.recall("active_campaigns", "campaigns")
        brand = await self.memory.recall("brand_guidelines", "brand")

        report = await self.think(
            f"""Generate the CMO daily marketing report.

## Your Tasks Today
{json.dumps(today_tasks, indent=2) if today_tasks else 'No CMO tasks today.'}

## Funnel Metrics
{funnel or 'Not tracked yet.'}

## Active Campaigns
{campaigns or 'None.'}

## Brand Status
{'Defined' if brand else 'Not defined yet.'}

Write a concise marketing report:
1. Content produced today (what was created/published)
2. Campaign progress and results
3. Funnel health (where are we strong/weak)
4. Community growth signals
5. Tomorrow's marketing priorities (top 3)
6. Marketing velocity: 🟢 green / 🟡 yellow / 🔴 red

Under 250 words. Be specific with numbers and results."""
        )

        await state_manager.save_daily_report(self.agent_id, report)
        return f"**CMO Marketing Report**\n{report}"
