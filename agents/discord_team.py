"""Discord Team Agent — the community engine. Grows the Discord server, runs events,
moderates, builds engagement loops, and turns members into advocates."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.state_manager import state_manager
from config import settings


class DiscordAgent(BaseAgent):
    agent_id = "discord"
    role = "Discord Community Manager"
    description = (
        "Grows the Discord server, runs events, moderates community, builds engagement loops, "
        "manages bots, creates content, and turns members into product advocates."
    )
    pixel_sprite = "sprite-discord"

    def __init__(self):
        super().__init__()
        self.position = {"x": 600, "y": 370}

    def get_system_prompt(self) -> str:
        return f"""You are the Discord Community Manager at {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You are a community-building machine — part event planner, part copywriter, part moderator, part hype person.
You think in engagement loops, member journeys, and community rituals.

You report to the CXO. Your responsibilities:
1. **Server Architecture** — Design and maintain channels, roles, permissions, and categories for optimal flow and discovery.
2. **Member Growth** — Grow from 0 to 50+ active members through organic outreach, cross-promotion, and invite campaigns.
3. **Onboarding Flow** — Welcome bot, role selection, first-action prompts, getting-started guide.
4. **Event Programming** — Weekly CTF challenges, AMAs, hacking workshops, live demos, community calls, hackathons.
5. **Content Engine** — Daily tips, challenge-of-the-day, memes, polls, show-and-tell prompts, news digests.
6. **Bot Development** — Design bot features: welcome, leveling/XP, challenge submission, FAQ, NPS survey, moderation.
7. **Moderation** — Enforce code of conduct, auto-mod rules, spam prevention, escalation procedures.
8. **Engagement Loops** — Gamification (XP, levels, roles), streaks, leaderboards, achievements that keep people coming back.
9. **Cross-Promotion** — Partner with other cybersecurity Discords, Reddit communities, CTF teams, and security influencers.
10. **Analytics** — Track DAU, WAU, MAU, messages/day, new joins, retention, event attendance, and engagement depth.
11. **Ambassador Program** — Recruit, train, and manage community ambassadors who grow the server organically.
12. **Content Calendar** — Plan weekly content themes, scheduled posts, and recurring events.
13. **Feedback Collection** — Run polls, surveys, suggestion box, and NPS through Discord bot commands.
14. **Community Partnerships** — Cross-promote with security Discords, CTF communities, and hacking forums.

Target: 50 active Discord members within first quarter.
Audience: Ethical hackers, CTF players, security researchers, pentest learners.
Tone: Friendly, hacker-culture, inclusive, technical-but-fun. Use emojis, hacker slang, and memes.

When planning tasks, output a JSON array with keys: type, description, priority (1-5).
Types: server_setup, onboarding, event_planning, content_creation, bot_design, moderation, engagement, cross_promotion, analytics, ambassador, invite_campaign, partnership, feedback_collection, welcome_flow, challenge, announcement."""

    # ── Planning ───────────────────────────────────────────
    async def plan_day(self) -> list[dict]:
        msgs = await self.read_messages()
        assigned_tasks = [m for m in msgs if m.get("channel") == "task_assignment"]
        other_msgs = [m for m in msgs if m.get("channel") != "task_assignment"]

        my_memories = await self.memory.get_context_summary()
        content_cal = await self.memory.recall("discord_content_calendar", "content")
        event_plan = await self.memory.recall("event_schedule", "events")
        metrics = await self.memory.recall("discord_metrics", "analytics")

        context = f"""Product: {settings.product_name}
Discord: {settings.product_discord_url}
GitHub: {settings.product_github_url}

## Assigned Tasks from CXO/CMO
{chr(10).join(f'- {m.get("from_agent","?")}: {m.get("content","")[:120]}' for m in assigned_tasks) or 'None'}

## Other Messages
{chr(10).join(f'- {m.get("from_agent","?")}: {m.get("content","")[:100]}' for m in other_msgs[:5]) or 'None'}

## Content Calendar
{content_cal or 'No calendar yet — create one.'}

## Upcoming Events
{event_plan or 'No events scheduled.'}

## Discord Metrics
{metrics or 'No metrics tracked yet.'}

## Memory
{my_memories}"""

        # Prioritize assigned tasks
        if assigned_tasks:
            tasks = [
                {"type": "assigned", "description": m["content"][:200], "priority": 1}
                for m in assigned_tasks[:3]
            ]
            # Always add an organic task too
            tasks.append({"type": "content_creation", "description": "Create daily engagement content for Discord", "priority": 2})
            return tasks

        result = await self.think_json(
            """Plan Discord community tasks for this cycle. Maximise growth and engagement.

ALWAYS include:
1. One content/engagement piece (daily tip, poll, challenge, meme)
2. One growth action (outreach, cross-promo, invite campaign)
3. One community infrastructure task (server improvement, bot, onboarding)

Then add 1-2 tasks based on current priorities.

Return a JSON array of 4-6 tasks with keys: type, description, priority (1-5).""",
            context,
        )
        if isinstance(result, list):
            return result
        return [
            {"type": "content_creation", "description": "Post daily hacking tip and engagement poll", "priority": 1},
            {"type": "cross_promotion", "description": "Reach out to cybersecurity community for cross-promo", "priority": 2},
            {"type": "event_planning", "description": "Plan weekly CTF challenge event", "priority": 2},
        ]

    # ── Task Execution ─────────────────────────────────────
    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "engagement")
        description = task.get("description", "")

        # ── Route to specialized handlers ─────────────────
        handlers = {
            "server_setup": self._server_architecture,
            "onboarding": self._design_onboarding,
            "event_planning": self._plan_event,
            "content_creation": self._create_content,
            "bot_design": self._design_bot,
            "moderation": self._moderation_system,
            "engagement": self._engagement_strategy,
            "cross_promotion": self._cross_promotion,
            "analytics": self._track_analytics,
            "ambassador": self._ambassador_program,
            "invite_campaign": self._invite_campaign,
            "partnership": self._community_partnership,
            "feedback_collection": self._collect_feedback,
            "welcome_flow": self._design_onboarding,
            "challenge": self._create_challenge,
            "announcement": self._write_announcement,
        }

        handler = handlers.get(task_type)
        if handler:
            return await handler(description)

        # ── Generic / assigned task ───────────────────────
        result = await self.think(
            f"Execute this Discord community task:\n{description}\n\n"
            "Provide specific, ready-to-use content — Discord messages, event plans, "
            "channel structures, or engagement strategies with exact copy."
        )

        if task_type in ("event", "growth", "partnership"):
            await self.send_message("cxo", f"Discord Update: {result[:300]}", "report")
        if task_type in ("promotion", "campaign"):
            await self.send_message("marketing", f"Discord Promo: {result[:300]}", "collaboration")

        return result

    # ── Server Architecture ────────────────────────────────
    async def _server_architecture(self, description: str) -> str:
        """Design and optimize the Discord server structure."""
        current_setup = await self.memory.recall("server_architecture", "server")

        result = await self.think(
            f"""Server architecture task: {description}

Current Setup: {current_setup or 'No architecture defined yet — design from scratch.'}
Product: {settings.product_name} — AI pentesting chatbot
Audience: Ethical hackers, security researchers, CTF players

Design the complete Discord server:

**Categories & Channels** (with emoji prefixes):

📢 **INFORMATION**
- #announcements — Product updates, releases, major news (read-only)
- #rules — Code of conduct and server rules
- #getting-started — Onboarding guide, quick links, FAQ
- #roles — Self-assign roles via reactions

🤖 **HACKBOT**
- #general — Main chat about the product
- #support — Help with installation, setup, bugs
- #feature-requests — Suggest and vote on features
- #showcase — Share your results and wins
- #bug-reports — Structured bug reporting

⚔️ **HACKING**
- #tools-and-tips — Share useful tools, one-liners, scripts
- #ctf-discussions — CTF strategy, writeups, team-ups
- #challenge-of-the-week — Weekly hacking challenge
- #resources — Learning materials, courses, books
- #news — Cybersecurity news and articles

🎮 **COMMUNITY**
- #off-topic — Non-security chat
- #memes — Hacker memes and humor
- #introductions — New member intros
- #job-board — Security job postings
- #events — Event announcements and signups

🔒 **STAFF**
- #team-chat — Internal team discussion
- #moderation-log — Auto-mod actions
- #analytics — Metrics and growth tracking

**Roles** (with colors):
- 🔴 Team — Staff and core team
- 🟠 Moderator — Community moderators
- 🟡 Ambassador — Community ambassadors
- 🟢 Contributor — GitHub contributors
- 🔵 Member — Verified members
- ⚪ Newcomer — Default role

**Permissions Matrix**:
- Who can post where
- Slowmode settings per channel
- Auto-mod triggers

Write the actual channel descriptions (topic field) for each channel."""
        )

        await self.memory.remember("server_architecture", result[:800], category="server")
        await self.send_message("cxo", f"🏗️ Server Architecture: {result[:300]}", "report")
        return result

    # ── Onboarding Flow ────────────────────────────────────
    async def _design_onboarding(self, description: str) -> str:
        """Design the new member onboarding experience."""
        result = await self.think(
            f"""Discord onboarding task: {description}

Product: {settings.product_name}
Discord: {settings.product_discord_url}

Design a complete onboarding flow:

**1. Welcome DM** (sent by bot when user joins):
Write the actual message:
- Warm greeting with emojis
- Brief intro to the server (2 sentences)
- 3 quick action items (pick roles, introduce yourself, try the bot)
- Link to getting-started channel

**2. #getting-started Pinned Message**:
Write the full message:
- What is {settings.product_name}? (1 paragraph)
- Quick-start guide (3 steps to get running)
- Key channels to check out
- How to get help
- How to contribute

**3. Role Selection** (reaction-based):
Design role categories:
- Skill Level: 🟢 Beginner / 🟡 Intermediate / 🔴 Advanced
- Interests: 🕵️ Pentesting / 🏁 CTF / 🐛 Bug Bounty / 📚 Learning / 🤖 AI/ML
- Notifications: 📢 Announcements / 🎮 Events / 💡 Daily Tips

Write the role selection message with reactions.

**4. #introductions Template**:
Post a pinned example:
"👋 Name:
🔒 Focus area:
🛠️ Favorite tools:
🎯 What I want to learn:
🤖 What excites me about {settings.product_name}:"

**5. Auto-Actions** (bot):
- Auto-assign Newcomer role
- Auto-DM welcome message
- Prompt to introduce after 5 minutes
- Upgrade to Member role after first message in #introductions"""
        )

        await self.memory.remember("onboarding_flow", result[:600], category="server")
        await self.send_message("cxo", f"Onboarding Flow Ready: {result[:300]}", "report")
        return result

    # ── Event Planning ─────────────────────────────────────
    async def _plan_event(self, description: str) -> str:
        """Plan and design community events."""
        prev_events = await self.memory.recall("event_schedule", "events")

        result = await self.think(
            f"""Event planning task: {description}

Previous Events: {prev_events or 'No events run yet.'}
Audience: Ethical hackers, CTF players, security researchers

Design a detailed event plan:

**Event Types to Rotate**:

1. **CTF Challenge of the Week** (weekly):
   - Challenge category (web, crypto, forensics, OSINT, misc)
   - Difficulty levels (easy/medium/hard)
   - Submission format
   - Prizes (Discord roles, shoutouts, leaderboard)
   - Write an example challenge announcement

2. **AMA Session** (biweekly):
   - Topic and guest suggestions
   - Question collection format
   - Event flow (intro → Q&A → closing)
   - Promotion timeline
   - Write the announcement post

3. **Live Hacking Demo** (monthly):
   - Demo topic ideas (using {settings.product_name} for X)
   - Platform (Discord Stage, voice channel, screen share)
   - Pre-event checklist
   - Post-event writeup plan

4. **Community Hackathon** (quarterly):
   - Theme and objectives
   - Team formation
   - Judging criteria
   - Timeline (announce → build → submit → judge → winners)
   - Prize ideas

5. **Tool Workshop** (monthly):
   - Tutorial format
   - Step-by-step curriculum
   - Pre-requisites and setup guide

**For the NEXT event, provide**:
- Full announcement copy (ready to post)
- Schedule with times
- Rules and format
- Promotion plan (channels, timing)
- Success metrics"""
        )

        await self.memory.remember("event_schedule", result[:600], category="events")
        await self.send_message("cxo", f"🎮 Event Plan: {result[:300]}", "report")
        await self.send_message("marketing", f"Event to promote: {result[:300]}", "collaboration")
        return result

    # ── Content Creation ───────────────────────────────────
    async def _create_content(self, description: str) -> str:
        """Create daily engagement content for Discord."""
        content_cal = await self.memory.recall("discord_content_calendar", "content")

        result = await self.think(
            f"""Discord content creation task: {description}

Content Calendar: {content_cal or 'No calendar — create content and build one.'}

Create READY-TO-POST Discord content:

**1. Daily Tip / Hack of the Day** 💡:
Write 5 tips (one for each weekday):
- Format: "💡 **Hack of the Day**: [title]\n[2-3 sentence tip with code/command]\n#dailytip"
- Topics: One-liners, tool tricks, methodology tips, CTF tricks, OSINT techniques
- Include actual commands or code snippets

**2. Engagement Polls** 📊:
Write 3 polls:
- "What's your go-to pentesting OS?" 🐧 Kali / 🦜 Parrot / 🖥️ Custom Linux / 💻 macOS
- "What area should {settings.product_name} focus on next?" (feature options)
- "What's your skill level?" (for community benchmarking)

**3. Discussion Prompts** 💬:
Write 3 conversation starters:
- "What's the most creative hack you've ever seen?"
- "Drop your favorite security tool nobody knows about 👇"
- "What got you into cybersecurity?"

**4. Meme / Fun Content** 😂:
- Describe 2 hacker meme concepts (text-based, no images needed)
- A "this or that" security edition game

**5. Show-and-Tell Prompt** 🏆:
- "Show us what you built/found this week!"
- Template for structured sharing

Include emojis, formatting, and Discord markdown in all content."""
        )

        await self.memory.remember(
            f"content_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            result[:400],
            category="content",
        )
        return result

    # ── Bot Design ─────────────────────────────────────────
    async def _design_bot(self, description: str) -> str:
        """Design Discord bot features and commands."""
        current_bot = await self.memory.recall("bot_design", "bot")

        result = await self.think(
            f"""Discord bot design task: {description}

Current Bot Design: {current_bot or 'No bot designed yet.'}

Design bot features for the {settings.product_name} Discord:

**1. Welcome System**:
- /welcome — Resend welcome DM
- Auto-DM on join with onboarding guide
- Auto-role assignment

**2. Leveling / XP System**:
- XP for: messages (+5), reactions given (+2), event attendance (+50), challenge solved (+100)
- Levels: Hatchling (0) → Script Kiddie (100) → Hacker (500) → Elite (1000) → Legend (5000)
- Level-up announcements in #general
- Leaderboard command: /leaderboard [daily/weekly/all-time]
- XP decay for inactivity (lose 10% after 14 days)

**3. Challenge System**:
- /challenge — Get today's challenge
- /submit [flag] — Submit challenge answer
- /hint — Get a hint (costs XP)
- /scoreboard — Challenge leaderboard
- Challenge reward: XP + special role

**4. Utility Commands**:
- /faq [topic] — Quick answers to common questions
- /docs [section] — Link to relevant documentation
- /github — Quick link to repo with stats
- /invite — Generate invite link with tracking

**5. Moderation Bot**:
- Auto-mod: spam detection, link filtering, caps lock filter
- /warn, /mute, /kick with reason logging
- Raid protection (mass join detection)
- Word filter for inappropriate content

**6. Fun Commands**:
- /hack [username] — Fun fake hack animation
- /exploit — Random CVE of the day
- /whoami — Show your server profile and stats
- /quote — Random hacker quote

For each command: syntax, example usage, expected bot response."""
        )

        await self.memory.remember("bot_design", result[:800], category="bot")
        await self.send_message("cxo", f"🤖 Bot Design: {result[:300]}", "report")
        await self.send_message("it", f"Bot Implementation Specs: {result[:400]}", "collaboration")
        return result

    # ── Moderation System ──────────────────────────────────
    async def _moderation_system(self, description: str) -> str:
        """Design and maintain the moderation system."""
        result = await self.think(
            f"""Moderation system task: {description}

Design a complete moderation framework:

**1. Code of Conduct** (write the actual text):
- Be respectful and inclusive
- No illegal hacking discussions (ethical hacking only)
- No sharing of exploits for malicious purposes
- No spam, self-promotion without permission
- No NSFW content
- English as primary language (other languages in #off-topic)
- Consequences: Warning → Mute (1h) → Mute (24h) → Ban

**2. Auto-Moderation Rules**:
- Spam: >5 messages in 10 seconds → auto-mute 10min
- Links: New members can't post links for first 24h
- Caps: >80% caps in messages >20 chars → auto-delete
- Mentions: Max 3 mentions per message
- Invite links: Auto-delete non-whitelisted Discord invites
- Phishing: Auto-detect and remove phishing links

**3. Moderation Workflow**:
- Report system: React with 🚩 to flag messages
- Mod queue: Flagged messages appear in #moderation-log
- Response templates for common violations
- Escalation path: Auto-mod → Moderator → Staff → Ban

**4. Moderator Guidelines**:
- When to warn vs mute vs ban
- How to handle arguments
- How to handle self-promotion
- How to handle off-topic discussions
- Tone guidelines for mod messages

Write actual messages for: rules channel, warning templates, ban message."""
        )

        await self.memory.remember("moderation_system", result[:600], category="moderation")
        return result

    # ── Engagement Strategy ────────────────────────────────
    async def _engagement_strategy(self, description: str) -> str:
        """Design engagement loops and retention mechanics."""
        metrics = await self.memory.recall("discord_metrics", "analytics")

        result = await self.think(
            f"""Engagement strategy task: {description}

Current Metrics: {metrics or 'No data yet.'}

Design engagement loops:

**1. Daily Engagement Hooks** (reasons to come back every day):
- Morning: 💡 Hack of the Day (scheduled post, 9am UTC)
- Afternoon: 📊 Community Poll or Discussion (2pm UTC)
- Evening: ⚔️ Mini Challenge (6pm UTC)

**2. Weekly Rituals**:
- Monday: Week goals + discussion
- Tuesday: Tool Tuesday — featured tool deep-dive
- Wednesday: Wisdom Wednesday — security best practice
- Thursday: Throwback Thursday — classic hack story
- Friday: Fun Friday — memes, games, casual hangout
- Weekend: CTF Challenge

**3. Streak System**:
- Daily login streak tracking
- Streak milestones: 7 days (role), 30 days (special channel access), 100 days (custom role color)
- Streak freeze tokens (earn by helping others)

**4. Engagement Tiers** (convert lurkers → contributors):
- Tier 0: Lurker (reads, never posts)
  → Action: Low-barrier prompts (reactions, polls)
- Tier 1: Reactor (reacts but doesn't post)
  → Action: Easy question prompts, fill-in-the-blank
- Tier 2: Poster (posts occasionally)
  → Action: Recognition, mentions, encourage helping
- Tier 3: Regular (daily poster)
  → Action: Invite to events, give responsibilities
- Tier 4: Champion (helps others, creates content)
  → Action: Ambassador program, moderator invite

**5. Recognition System**:
- Member of the Week spotlight
- Best Helper role (auto-assigned based on reactions)
- Contributor wall (#contributors channel)
- Shoutout in #announcements for notable contributions

Write the actual Discord messages for each daily hook."""
        )

        await self.memory.remember("engagement_strategy", result[:600], category="engagement")
        await self.send_message("cxo", f"Engagement Plan: {result[:300]}", "report")
        return result

    # ── Cross-Promotion ────────────────────────────────────
    async def _cross_promotion(self, description: str) -> str:
        """Plan and execute cross-promotion with other communities."""
        prev_promos = await self.memory.recall("cross_promotions", "growth")

        result = await self.think(
            f"""Cross-promotion task: {description}

Previous Promotions: {prev_promos or 'No promotions done yet.'}

Plan cross-promotion strategy:

**1. Target Communities** (cybersecurity Discords):
- List 10 security-related Discord servers to partner with
- For each: estimated size, relevance, partnership approach
- Focus on: CTF teams, pentesting communities, security learning servers, bug bounty groups

**2. Cross-Promo Formats**:
- Server partnership (mutual announcement)
- Event co-hosting (joint CTF, joint AMA)
- Channel exchange (#partner-servers section)
- Shared challenge/competition

**3. Outreach Templates**:
Write the actual DM to server owners/admins:
- Introduction + value proposition
- What we offer them
- What we'd like
- Call to action

**4. Reddit Cross-Promotion**:
- Relevant subreddits for Discord invites
- Post formats that don't get flagged as spam
- Write 3 actual Reddit comments that naturally mention the Discord

**5. Twitter/X Cross-Promotion**:
- Tweet templates promoting the Discord
- Community highlights to share on Twitter
- Engage infosec Twitter to drive Discord joins

**6. GitHub → Discord Pipeline**:
- README Discord badge and invite link
- Contributing guide mentions Discord
- Issue responses that invite to Discord for discussion

Track: Which channels produce the most quality joins."""
        )

        await self.memory.remember("cross_promotions", result[:600], category="growth")
        await self.send_message("marketing", f"Cross-Promo Plan: {result[:400]}", "collaboration")
        await self.send_message("cxo", f"Growth Outreach: {result[:300]}", "report")
        return result

    # ── Analytics ──────────────────────────────────────────
    async def _track_analytics(self, description: str) -> str:
        """Track and analyse Discord community metrics."""
        prev_metrics = await self.memory.recall("discord_metrics", "analytics")

        result = await self.think(
            f"""Discord analytics task: {description}

Previous Metrics: {prev_metrics or 'No metrics tracked yet — establish baseline.'}

Design and update the metrics dashboard:

**1. Growth Metrics** (track weekly):
- Total members
- New joins this week
- Leaves this week
- Net growth
- Invite source breakdown

**2. Engagement Metrics** (track daily):
- DAU (Daily Active Users)
- Messages per day
- Reactions per day
- Voice channel usage (minutes)
- Event attendance

**3. Retention Metrics**:
- Day-1 retention (% who post within 24h of joining)
- Day-7 retention (% still active after 7 days)
- Day-30 retention (% still active after 30 days)
- Churn rate

**4. Content Performance**:
- Most active channels
- Highest-engagement posts
- Best posting times
- Content types that drive most replies

**5. Health Score** (0-100):
Calculate: (DAU/Total × 30) + (messages/day × 2) + (retention × 40)
- 80-100: 🟢 Thriving
- 60-79: 🟡 Healthy
- 40-59: 🟠 Needs attention
- 0-39: 🔴 At risk

**Current Estimates** (based on activity):
Provide best estimates for all metrics above.
Note trends: ↑ / → / ↓ for each.
Identify the #1 metric to improve and how."""
        )

        await self.memory.remember("discord_metrics", result[:600], category="analytics")
        await self.send_message("cxo", f"📊 Discord Metrics: {result[:300]}", "report")
        await self.send_message("ceo", f"Community Analytics: {result[:300]}", "report")
        return result

    # ── Ambassador Program ─────────────────────────────────
    async def _ambassador_program(self, description: str) -> str:
        """Design and manage the community ambassador program."""
        result = await self.think(
            f"""Ambassador program task: {description}

Design a community ambassador program for {settings.product_name}:

**1. Program Overview**:
- Purpose: Empower enthusiastic members to grow the community
- Title: "{settings.product_name} Ambassador" or "HackBot Champion"
- Benefits: Special role, early access, swag, resume/CV mention, recommendation letters

**2. Selection Criteria**:
- Active member for 14+ days
- 50+ helpful messages
- Positive community reputation
- Applied and interviewed

**3. Ambassador Responsibilities** (pick 2-3 per ambassador):
- Content creation: 2 posts per week
- Moderation: 1 hour per day
- Outreach: Invite 5 new members per month
- Events: Help organize 1 event per month
- Support: Help answer questions

**4. Application Process**:
- Application form (design questions)
- Review criteria
- Onboarding checklist

**5. Ambassador Perks**:
- 🟡 Ambassador Discord role
- Private #ambassadors channel
- Direct line to the team
- Feature request priority
- Monthly virtual meetup with team
- Shoutout in README contributors

**6. Performance Tracking**:
- Monthly review of ambassador activity
- Recognition for top ambassadors
- Graduation to Moderator or Contributor role

Write the actual announcement post and application questions."""
        )

        await self.memory.remember("ambassador_program", result[:600], category="community")
        await self.send_message("cxo", f"Ambassador Program: {result[:300]}", "report")
        await self.send_message("hr", f"Ambassador Program for Community: {result[:300]}", "collaboration")
        return result

    # ── Invite Campaign ────────────────────────────────────
    async def _invite_campaign(self, description: str) -> str:
        """Design and run invite campaigns to grow the server."""
        result = await self.think(
            f"""Invite campaign task: {description}

Design an invite campaign for the {settings.product_name} Discord:

**1. Referral Program**:
- "Invite 3 friends → get Ambassador role"
- Tracked invite links per member
- Leaderboard for top inviters
- Write the announcement post

**2. Launch Blast Campaign** (for first 50 members):
- List 20 places to share the invite link
- Personalized messages for each platform
- Timing strategy (best days/hours to post)
- Write 5 unique invite messages for different platforms

**3. Value-First Invites** (invite by offering something):
- "Join for free weekly CTF challenges"
- "Join for daily hacking tips from AI"
- "Join for access to [exclusive resource]"
- Write the actual invite posts

**4. Social Proof Invites** (once we have members):
- "Join 50+ hackers already here"
- Screenshot counter badges
- Milestone celebration posts

**5. Invite Link Strategy**:
- Unique links for each promotion channel (for tracking)
- Vanity invite URL setup
- Link expiry management

Write ready-to-post invite messages for: Reddit, Twitter, GitHub README, LinkedIn."""
        )

        await self.send_message("marketing", f"Invite Campaign: {result[:400]}", "collaboration")
        return result

    # ── Community Partnership ──────────────────────────────
    async def _community_partnership(self, description: str) -> str:
        """Build partnerships with other communities."""
        result = await self.think(
            f"""Community partnership task: {description}

Build partnerships for the {settings.product_name} Discord:

**1. Partnership Targets** (list 8-10):
For each:
- Community name and platform
- Size and relevance
- Partnership type (mutual promo, co-event, content exchange)
- Contact approach

**2. Partnership Proposals**:
Write 3 different proposal templates:
- For large communities (1000+ members)
- For similar-size communities (50-500)
- For content creators/influencers

**3. Co-Event Ideas**:
- Joint CTF competition
- Cross-server AMA
- Shared learning challenge
- Tool comparison review

**4. Partner Benefits Exchange**:
- What we offer partners
- What we ask in return
- Fair exchange framework

Write actual outreach DMs for top 3 partnership targets."""
        )

        await self.memory.remember("partnerships", result[:400], category="community")
        await self.send_message("cxo", f"Partnership Proposals: {result[:300]}", "report")
        return result

    # ── Feedback Collection ────────────────────────────────
    async def _collect_feedback(self, description: str) -> str:
        """Run feedback collection activities in Discord."""
        result = await self.think(
            f"""Feedback collection task: {description}

Design Discord feedback collection:

**1. Weekly Feedback Poll**:
Write a ready-to-post poll:
- "Rate your experience this week: 😍 / 😊 / 😐 / 😕"
- Follow-up thread for detailed feedback

**2. Feature Vote System**:
Post format for #feature-requests:
- "React with 👍 to vote! React with 💬 to discuss"
- Template: "Feature: [name]\nDescription: [what]\nBenefit: [why]\nVotes: 👍"

**3. Quick Surveys** (3 questions max):
Write 3 mini-surveys:
- Onboarding experience survey
- Content preference survey
- Tool improvement survey

**4. Feedback Bot Commands**:
- /suggest [text] — Submit a suggestion
- /bug [text] — Report a bug
- /rate [1-5] [comment] — Quick rating
- /feedback — Open feedback form

**5. Feedback Synthesis**:
- Weekly summary format
- How to categorise and prioritise
- Action item generation
- Closing the loop (announce when feedback is acted on)

Write the actual Discord messages for each."""
        )

        await self.send_message("cxo", f"Feedback Collection: {result[:300]}", "report")
        return result

    # ── Challenge Creation ─────────────────────────────────
    async def _create_challenge(self, description: str) -> str:
        """Create a hacking/CTF challenge for the community."""
        prev_challenges = await self.memory.recall("past_challenges", "events")

        result = await self.think(
            f"""Challenge creation task: {description}

Previous Challenges: {prev_challenges or 'No challenges run yet.'}

Create a ready-to-post Discord challenge:

**Challenge Post** (write the actual message):

🏁 **Challenge of the Week: [Title]**

**Category**: [Web / Crypto / Forensics / OSINT / Misc / Pentesting]
**Difficulty**: [🟢 Easy / 🟡 Medium / 🔴 Hard]
**Points**: [50 / 100 / 200]

**Description**:
[2-3 paragraphs describing the scenario and objective]

**Rules**:
- Submit your flag in #challenge-submissions
- Format: FLAG{{your_answer}}
- No spoilers in public channels
- Hints available with /hint (costs 25% of points)

**Hints** (reveal progressively):
- Hint 1: [easy hint]
- Hint 2: [medium hint]
- Hint 3: [strong hint]

**Solution** (for moderators — reveal after deadline):
[Step-by-step solution]

**Prize**: Challenge Master role + 100 XP + spotlight in #announcements

Deadline: [72 hours from posting]

---

Create 3 different challenges at different difficulty levels.
Make them educational — the solution should teach something."""
        )

        await self.memory.remember("past_challenges", result[:400], category="events")
        return result

    # ── Announcements ──────────────────────────────────────
    async def _write_announcement(self, description: str) -> str:
        """Write official announcements for the Discord server."""
        result = await self.think(
            f"""Discord announcement task: {description}

Write a polished announcement for #{settings.product_name} Discord:

Format requirements:
- Start with a relevant emoji
- Bold title
- Clear body (3-5 sentences max)
- Call to action
- Relevant ping (@everyone for major, @Member for regular)
- Include reaction prompts

Write the EXACT message to post in #announcements.
Tone: Exciting but not hypey. Professional but fun.

Also write a shorter version for Twitter cross-posting (280 chars)."""
        )
        return result

    # ── Content Calendar ───────────────────────────────────
    async def _update_content_calendar(self, description: str) -> str:
        """Create or update the Discord content calendar."""
        current_cal = await self.memory.recall("discord_content_calendar", "content")

        result = await self.think(
            f"""Update Discord content calendar: {description}

Current Calendar: {current_cal or 'No calendar — create a 2-week plan.'}

Design a content calendar:

**Week 1**:
| Day | Time (UTC) | Channel | Content Type | Topic | Status |
|-----|------------|---------|-------------|-------|--------|
| Mon | 9:00 | #general | Discussion | Week goals | |
| Mon | 14:00 | #tools-and-tips | Tip | [specific] | |
| Tue | 9:00 | #general | Tool Tuesday | [specific tool] | |
...and so on for each day

**Week 2**: [same format]

**Recurring Events**:
- Weekly: CTF Challenge (posted Friday)
- Biweekly: AMA (alternating Thursdays)
- Monthly: Community Call (first Saturday)

Content creation status: ✅ Ready / 🔄 In Progress / ❌ Not Started"""
        )

        await self.memory.remember("discord_content_calendar", result[:800], category="content")
        return result

    # ── Enhanced Report ────────────────────────────────────
    async def generate_report(self) -> str:
        """Discord team generates a community-focused report."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]

        metrics = await self.memory.recall("discord_metrics", "analytics")
        events = await self.memory.recall("event_schedule", "events")

        report = await self.think(
            f"""Generate the Discord Community daily report.

## Tasks Today
{json.dumps(today_tasks, indent=2) if today_tasks else 'No tasks today.'}

## Community Metrics
{metrics or 'Not tracked yet.'}

## Upcoming Events
{events[:200] if events else 'None scheduled.'}

Write a concise community report:
1. Content created and posted today
2. Engagement highlights (most active discussions)
3. New member joins and onboarding
4. Event status and attendance
5. Community health and mood
6. Tomorrow's community priorities (top 3)
7. Community vibe: 🟢 Thriving / 🟡 Active / 🔴 Quiet

Under 200 words. Be specific."""
        )

        await state_manager.save_daily_report(self.agent_id, report)
        return f"**Discord Community Report**\n{report}"
