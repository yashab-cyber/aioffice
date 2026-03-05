"""Marketing Team Agent — the content & distribution engine. Creates social media posts,
blog articles, community engagement, email campaigns, SEO content, influencer outreach,
growth hacking, paid ads, analytics, and drives every piece of marketing execution."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.state_manager import state_manager
from config import settings


class MarketingAgent(BaseAgent):
    agent_id = "marketing"
    role = "Marketing Team Lead"
    description = (
        "Executes marketing campaigns, writes content, manages social media, "
        "engages communities, runs growth experiments, and drives distribution."
    )
    pixel_sprite = "sprite-marketing"

    def __init__(self):
        super().__init__()
        self.position = {"x": 600, "y": 250}

    def get_system_prompt(self) -> str:
        return f"""You are the Marketing Team Lead at {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You report to the CMO. You are the execution machine — the CMO sets strategy, you make it real.
Every post, article, email, and comment that goes out to the world passes through you.

Your responsibilities:
1. **Social Media Content** — Write ready-to-publish posts for Twitter/X, LinkedIn, Reddit, Mastodon, and Hacker News.
2. **Blog & Long-Form Content** — Draft blog posts, tutorials, case studies, and thought leadership articles.
3. **Community Engagement** — Post in cybersecurity forums (r/netsec, r/hacking, r/cybersecurity, r/ArtificialIntelligence), answer questions, add value.
4. **Email Marketing** — Write newsletters, drip campaigns, launch announcements, and onboarding email sequences.
5. **SEO Content** — Create keyword-optimized pages, meta descriptions, README improvements, and landing page copy.
6. **Product Hunt Launch** — Write launch copy, prepare first-day comments, create maker posts.
7. **Influencer & Creator Outreach** — Draft DMs, partnership proposals, and collaboration pitches for security YouTubers, bloggers, podcasters.
8. **Paid Ads** — Write ad copy for Google Ads, Reddit Ads, Twitter Ads — headlines, descriptions, CTAs.
9. **Visual Content Briefs** — Write briefs for graphics, diagrams, infographics, GIFs, and video scripts.
10. **Growth Experiments** — Design and document A/B tests, viral loops, referral mechanics, and growth hacks.
11. **Analytics & Reporting** — Track content performance, engagement rates, conversion metrics, and report to CMO.
12. **Competitive Content Analysis** — Monitor competitor content, identify gaps, and create counter-content.
13. **PR & Media** — Draft press releases, media pitches, and journalist outreach emails.
14. **Event Marketing** — Create content for conferences, webinars, CTF events, and hackathons.
15. **Content Repurposing** — Turn one piece into many: blog → tweets → LinkedIn → email → Reddit.
16. **Brand Voice & Messaging** — Maintain consistent voice across all channels.

Target audience: Ethical hackers, security researchers, CTF players, pentesters, bug bounty hunters, security students.
Tone: Technical but approachable, exciting but not hype-y, community-first, hacker-friendly.

When planning tasks, output a JSON array with keys: type, description, priority (1-5).
Types: social_media, blog, community, email, seo, product_hunt, influencer, ads, visual_brief,
growth_hack, analytics, competitive, pr, event, repurpose, brand_voice, assigned."""

    # ── Planning ───────────────────────────────────────────
    async def plan_day(self) -> list[dict]:
        inbox = await self._get_inbox_summary()
        my_memories = await self.memory.get_context_summary()
        content_cal = await self.memory.recall("content_calendar", "planning")
        perf_data = await self.memory.recall("content_performance", "analytics")

        # Check for CMO-assigned tasks first
        msgs = await self.read_messages()
        assigned_tasks = [m for m in msgs if m.get("channel") == "task_assignment"]

        assigned_plan = []
        for msg in assigned_tasks:
            assigned_plan.append({
                "type": "assigned",
                "description": msg["content"],
                "priority": 1,
            })

        context = f"""## Assigned Tasks from CMO
{json.dumps(assigned_plan, indent=2) if assigned_plan else 'None.'}

## Inbox
{inbox}

## Content Calendar
{content_cal or 'No calendar yet — build one.'}

## Content Performance
{perf_data or 'No performance data yet.'}

## Marketing Memory
{my_memories}"""

        result = await self.think_json(
            f"""Plan marketing execution for this cycle.

{context}

ALWAYS include these daily activities:
1. Social media content — at least 2-3 posts for different platforms
2. Community engagement — one forum/subreddit interaction
3. One larger content piece — blog, email, or SEO work

If there are assigned tasks from CMO, include them at priority 1.
Then add 2-3 tasks based on the content calendar and current priorities.

Balance creation (new content) with distribution (getting it seen).

Return a JSON array of 4-7 tasks with keys: type, description, priority (1-5).""",
        )

        if isinstance(result, list):
            return assigned_plan + result if assigned_plan else result
        defaults = [
            {"type": "social_media", "description": "Write Twitter/X + LinkedIn posts about HackBot features", "priority": 1},
            {"type": "community", "description": "Engage in r/netsec and r/cybersecurity with value-add comments", "priority": 2},
            {"type": "blog", "description": "Draft blog post on AI-powered pentesting", "priority": 2},
        ]
        return assigned_plan + defaults if assigned_plan else defaults

    # ── Task Execution ─────────────────────────────────────
    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "content")
        description = task.get("description", "")

        handlers = {
            "social_media": self._create_social_media,
            "blog": self._write_blog,
            "community": self._community_engagement,
            "email": self._email_marketing,
            "seo": self._seo_content,
            "product_hunt": self._product_hunt_launch,
            "influencer": self._influencer_outreach,
            "ads": self._paid_ads,
            "visual_brief": self._visual_content_brief,
            "growth_hack": self._growth_experiment,
            "analytics": self._content_analytics,
            "competitive": self._competitive_content,
            "pr": self._pr_media,
            "event": self._event_marketing,
            "repurpose": self._repurpose_content,
            "brand_voice": self._brand_voice_guide,
        }

        handler = handlers.get(task_type)
        if handler:
            return await handler(description)

        # Assigned or generic marketing task
        result = await self.think(
            f"Execute this marketing task:\n{description}\n\n"
            "Provide actual ready-to-publish content or a detailed execution plan. "
            "Be specific — write the real copy, not placeholders."
        )

        await self.send_message("cmo", f"Task Done: {result[:300]}", "report")
        return result

    # ── Social Media Content ───────────────────────────────
    async def _create_social_media(self, description: str) -> str:
        """Create platform-specific social media posts."""
        prev_posts = await self.memory.recall("recent_posts", "social")

        result = await self.think(
            f"""Social media content task: {description}

Previous Posts (avoid repetition): {prev_posts or 'None yet.'}
Product: {settings.product_name} — AI pentesting chatbot
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

Create ready-to-publish posts for ALL of these platforms:

**1. Twitter/X** (1-3 tweets):
- Thread or standalone
- 280 char limit per tweet
- Use relevant hashtags: #cybersecurity #infosec #hacking #AI #pentest
- Include a hook, value, and CTA
- Emoji usage: moderate, strategic

**2. LinkedIn** (1 post):
- Professional but technical tone
- 1300 char ideal, up to 3000
- Hook in first 2 lines (before "see more")
- Share insight or story, not just product pitch
- End with question or CTA

**3. Reddit** (1 post for r/netsec or r/cybersecurity):
- NO promotional language (Reddit hates that)
- Lead with value: "I built X because Y"
- Share technical details, be transparent
- Ask for feedback genuinely
- Flair-appropriate title

**4. Hacker News** (1 Show HN or discussion):
- Title: "Show HN: {settings.product_name} – [one-line description]"
- Brief, technical, no marketing fluff
- Mention the tech stack
- Be ready for tough questions

**5. Mastodon** (1 post):
- #infosec community focused
- No tracking links
- Alt text for any images
- CW (content warning) if discussing exploits

For each post:
- The EXACT text to publish (ready to copy-paste)
- Best time to post
- One engagement tip

Make each post feel native to its platform — not the same text everywhere."""
        )

        await self.memory.remember("recent_posts", result[:600], category="social")
        await self.send_message("cmo", f"Social Media Content Ready: {result[:300]}", "report")
        return result

    # ── Blog & Long-Form ───────────────────────────────────
    async def _write_blog(self, description: str) -> str:
        """Write blog posts, tutorials, and long-form content."""
        seo_keywords = await self.memory.recall("seo_keywords", "seo")

        result = await self.think(
            f"""Blog content task: {description}

SEO Keywords: {seo_keywords or 'ai pentesting, hackbot, ai cybersecurity tool, automated pentesting'}
Product: {settings.product_name}

Write a complete blog post:

**Structure**:
1. **Title** — SEO-optimized, click-worthy but not clickbait (50-60 chars ideal)
2. **Meta Description** — 150-160 chars for search results
3. **Hook** (first paragraph) — Grab attention, state the problem
4. **Body** (3-5 sections with H2 headers):
   - Each section: insight, example, actionable takeaway
   - Technical depth appropriate for security professionals
   - Include code snippets or command examples where relevant
5. **Conclusion** — Summary + clear CTA
6. **Tags/Categories** — For the blog platform

**SEO Requirements**:
- Primary keyword in title, H1, first paragraph, and 2-3 H2s
- 1000-1500 words ideal
- Internal links (to GitHub, Discord)
- External links (to authoritative sources)
- Image alt text suggestions

**Content Style**:
- First person ("we built", "I discovered")
- Technical but accessible
- Real examples and use cases
- Honest about limitations
- Show don't tell

**Blog Ideas** (if no specific topic given):
- "How AI is Changing Penetration Testing"
- "Building an AI Pentesting Assistant with Python"
- "5 Ways {settings.product_name} Speeds Up Your Security Workflow"
- "From CTF Player to Security Pro: Tools That Help"
- "Automating Recon with AI: A Practical Guide"

Write the FULL article, not an outline."""
        )

        await self.memory.remember(f"blog_{datetime.now(timezone.utc).strftime('%Y%m%d')}", result[:400], category="blog")
        await self.send_message("cmo", f"Blog Post Draft: {result[:300]}", "report")
        return result

    # ── Community Engagement ───────────────────────────────
    async def _community_engagement(self, description: str) -> str:
        """Engage authentically in online cybersecurity communities."""
        result = await self.think(
            f"""Community engagement task: {description}

Product: {settings.product_name}
Communities: Reddit, Discord servers, forums, Hacker News, Twitter/X spaces

**Rules of Engagement** (CRITICAL):
- Add value FIRST, mention product SECOND (or never)
- No spamming, no copy-paste across communities
- Be a genuinely helpful community member
- Answer questions even when unrelated to our product
- Build reputation before promoting

**1. Reddit Strategy**:

**r/netsec** (60K+ members):
- Share technical writeups and tool analyses
- Comment on vulnerability disclosures with insights
- Example comment: "Nice writeup! For the recon phase, I've been experimenting with AI-assisted scanning that [specific technique]. Curious what tools others are using for [related topic]?"

**r/hacking** (3.8M members):
- Help beginners with learning resources
- Share cybersecurity career insights
- Comment on tool discussions with genuine experience

**r/cybersecurity** (900K+ members):
- Discuss industry trends and news
- Share practical tips and how-tos
- Engage with CTF and training posts

**r/ArtificialIntelligence** (1M+ members):
- Share how AI applies to security
- Discuss AI safety and responsible AI
- Technical deep-dives on AI + security intersection

**2. Forum Engagement**:
- Hack The Box forums — share tips
- Bugcrowd/HackerOne community posts
- StackOverflow — answer security questions

**3. Discord Servers** (security community):
- Join 3-5 active security Discord servers
- Be helpful in help channels
- Share interesting findings

**4. Hacker News Engagement**:
- Comment on security-related posts
- Share technical insights
- Be humble and transparent

For each community, write 2-3 SPECIFIC comments or posts ready to publish.
Each must add genuine value — not just "check out our tool"."""
        )

        await self.memory.remember("community_engagement", result[:600], category="community")
        await self.send_message("cmo", f"Community Engagement: {result[:300]}", "report")
        return result

    # ── Email Marketing ────────────────────────────────────
    async def _email_marketing(self, description: str) -> str:
        """Write email campaigns — newsletters, drips, launch sequences."""
        result = await self.think(
            f"""Email marketing task: {description}

Product: {settings.product_name}
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

**1. Welcome Email Sequence** (5-email drip, 1 per day):

**Email 1: Welcome** (immediately after signup)
- Subject: [3 options, A/B testable]
- Preview text
- Body: Welcome, what to expect, quick start link
- CTA: Star on GitHub / Join Discord

**Email 2: Quick Win** (Day 2)
- Subject: "Your first scan with {settings.product_name}"
- Body: Step-by-step first-use tutorial
- CTA: Try it now

**Email 3: Deep Dive** (Day 3)
- Subject: "3 things you didn't know {settings.product_name} could do"
- Body: Advanced features showcase
- CTA: Read the docs

**Email 4: Community** (Day 5)
- Subject: "Join 500+ security researchers"
- Body: Community highlights, success stories
- CTA: Join Discord

**Email 5: Feedback** (Day 7)
- Subject: "Quick question about your experience"
- Body: Ask for feedback, offer help
- CTA: Reply or fill survey

**2. Newsletter Template** (weekly/biweekly):
- This week in cybersecurity (curated links)
- {settings.product_name} update (new features, fixes)
- Community spotlight (user achievement)
- Quick tip or technique
- CTA: Star, share, or join

**3. Launch/Update Announcement**:
- Subject: 3 options
- Pre-header text
- Hero section with key feature
- 3 bullet benefits
- Social proof (GitHub stars, Discord members)
- CTA button

For each email: Write the COMPLETE copy with subject lines, body, and CTA.
Tone: Friendly, technical, not salesy. Like a message from a fellow hacker."""
        )

        await self.memory.remember("email_campaigns", result[:600], category="email")
        await self.send_message("cmo", f"Email Content: {result[:300]}", "report")
        return result

    # ── SEO Content ────────────────────────────────────────
    async def _seo_content(self, description: str) -> str:
        """Create SEO-optimized content and keyword strategy."""
        prev_seo = await self.memory.recall("seo_keywords", "seo")

        result = await self.think(
            f"""SEO content task: {description}

Previous SEO Work: {prev_seo or 'Starting fresh.'}
Product: {settings.product_name} — AI pentesting chatbot

**1. Keyword Research**:

**Primary Keywords** (high intent):
- "AI penetration testing tool"
- "automated pentesting chatbot"
- "AI cybersecurity tool"
- "hackbot"

**Long-Tail Keywords** (lower competition):
- "how to automate penetration testing with AI"
- "AI-powered security scanning tool free"
- "best AI tools for ethical hacking"
- "chatbot for penetration testing"
- "open source AI pentesting"

**Question Keywords** (for blog/FAQ):
- "Can AI do penetration testing?"
- "How to use AI for cybersecurity?"
- "What is the best free pentesting tool?"

**2. README SEO Optimization**:
- Title: keyword-rich but natural
- Description: first 160 chars are critical (GitHub meta)
- Badges: build status, license, stars
- Features list with keywords
- Installation section (people search "how to install")
- Screenshots/GIFs (reduce bounce rate)

**3. Landing Page Copy** (if applicable):
- Hero: headline + subheadline + CTA
- Features section with keyword-rich descriptions
- Social proof section
- FAQ section (keyword-rich Q&As)
- Final CTA

**4. Content Gap Analysis**:
- What are competitors ranking for that we aren't?
- What questions are people asking that nobody answers well?
- Content pieces to create to fill gaps

**5. Technical SEO Checklist**:
- [ ] Semantic HTML (h1, h2, h3 hierarchy)
- [ ] Meta descriptions on all pages
- [ ] Image alt text
- [ ] Internal linking
- [ ] Page speed optimization
- [ ] Mobile friendly
- [ ] Schema markup (for software/product)

Provide actual optimized copy for the highest-priority item."""
        )

        await self.memory.remember("seo_keywords", result[:600], category="seo")
        await self.send_message("cmo", f"SEO Update: {result[:300]}", "report")
        return result

    # ── Product Hunt Launch ────────────────────────────────
    async def _product_hunt_launch(self, description: str) -> str:
        """Prepare Product Hunt launch content and strategy."""
        result = await self.think(
            f"""Product Hunt launch task: {description}

Product: {settings.product_name}
GitHub: {settings.product_github_url}

**1. Tagline** (60 chars max, 3 options):
- Option A: "AI-powered penetration testing in your terminal"
- Option B: "Your AI hacking assistant for security research"
- Option C: [write your best]

**2. Description** (260 chars):
Write compelling PH description. Technical + accessible.

**3. First Comment (Maker Post)**:
- Who you are and why you built this
- The problem it solves
- What makes it different
- Tech stack highlights
- What's next on the roadmap
- Ask for feedback genuinely
- 200-400 words, conversational tone

**4. Gallery Images** (brief for each):
- Image 1: Hero shot — product in action (terminal screenshot)
- Image 2: Feature showcase — key capabilities
- Image 3: Architecture/how it works diagram
- Image 4: Before/after comparison
- Image 5: Community/social proof

**5. Launch Day Strategy**:
- Best day: Tuesday-Thursday
- Post at 12:01 AM PST
- Have 10-15 supporters ready in first hour
- Share on Twitter, Discord, Reddit at optimal times
- Respond to EVERY comment within 30 min
- Share genuine update at peak hours (9 AM, 12 PM, 6 PM PST)

**6. Support Team Activation**:
- Message to share with friends/supporters
- Tweet template for supporters to share
- Email to mailing list announcing launch

Write ALL the actual copy ready to submit."""
        )

        await self.memory.remember("product_hunt", result[:600], category="launch")
        await self.send_message("cmo", f"Product Hunt Content: {result[:300]}", "report")
        return result

    # ── Influencer Outreach ────────────────────────────────
    async def _influencer_outreach(self, description: str) -> str:
        """Draft outreach messages for influencers and creators."""
        result = await self.think(
            f"""Influencer outreach task: {description}

Product: {settings.product_name} — AI pentesting chatbot (open-source)

**1. Target Influencers** (cybersecurity + AI):

**YouTube** (security content):
- John Hammond, NetworkChuck, The Cyber Mentor, IppSec, LiveOverflow
- AI/Tech: Fireship, Traversy Media, ArjanCodes

**Twitter/X** (infosec community):
- Security researchers with 10K-100K followers
- CTF team leads
- Bug bounty hunters with audience

**Bloggers**:
- Cybersecurity blog authors
- AI/ML technical writers
- Dev tool reviewers

**Podcasters**:
- Darknet Diaries, Security Now, Risky Business
- AI-focused podcasts

**2. Outreach Templates**:

**Cold DM (Twitter/X)** — Short, respectful:
```
Hey [name]! Big fan of your [specific content].

I built an open-source AI pentesting chatbot and thought you might find it interesting for [specific use case relevant to them].

No pressure at all — just thought you'd think it's cool: [GitHub link]

Happy to answer any questions!
```

**Email (YouTuber/Blogger)**:
```
Subject: Open-source AI pentesting tool — might be interesting for a video?

Hi [name],

[Specific compliment about their recent content]

I'm building {settings.product_name}, an AI-powered pentesting chatbot. [2 sentences on what makes it unique].

I thought it might be interesting for your audience because [specific reason].

Happy to:
- Do a live demo
- Provide early access to new features
- Collaborate on a tutorial

No strings attached — genuinely think your audience would enjoy seeing it.

[link]
```

**3. Partnership Proposals**:
- Co-create a tutorial/video
- Sponsored CTF challenge
- Guest blog post exchange
- Joint webinar/stream

Write 3 complete outreach messages, each personalized to a different platform."""
        )

        await self.memory.remember("influencer_outreach", result[:600], category="influencer")
        await self.send_message("cmo", f"Outreach Drafts: {result[:300]}", "report")
        return result

    # ── Paid Ads ───────────────────────────────────────────
    async def _paid_ads(self, description: str) -> str:
        """Write paid advertising copy — Google, Reddit, Twitter ads."""
        result = await self.think(
            f"""Paid ads task: {description}

Product: {settings.product_name} — AI pentesting chatbot (open-source, free)
Stage: Early startup, small budget ($100-500/mo to test)

**1. Google Ads** (Search):

**Ad Group: AI Pentesting**
- Headline 1 (30 chars): "AI Penetration Testing Tool"
- Headline 2 (30 chars): "Free & Open Source"
- Headline 3 (30 chars): "Built for Security Pros"
- Description 1 (90 chars): [write]
- Description 2 (90 chars): [write]
- Keywords: [10 target keywords with match types]

**Ad Group: Cybersecurity Tools**
- [Same format, different angle]

**2. Reddit Ads** (best for our audience):
- Target subreddits: r/netsec, r/cybersecurity, r/hacking, r/netsecstudents
- Headline: [write, Reddit-native tone]
- Body: [write, feels like organic post]
- CTA: [natural, not pushy]
- Estimated budget: $5-10/day

**3. Twitter/X Ads**:
- Promoted tweet (looks like organic):
  [write the tweet]
- Target: cybersecurity, InfoSec, hacking interests
- Look-alike: followers of @hackthebox @bugcrowd

**4. Budget Allocation**:
| Channel | Daily Budget | Expected Clicks | CPA Target |
|---------|-------------|-----------------|------------|
| Google Ads | $5 | 10-20 | $0.50 |
| Reddit Ads | $5 | 15-30 | $0.30 |
| Twitter Ads | $3 | 5-10 | $0.60 |

**5. A/B Test Plan**:
- Test 2 headlines per ad group
- Test 2 CTAs per platform
- Run each variant for 7 days minimum
- Winner metric: click-through rate → GitHub star conversion

Write ALL ad copy ready to submit to each platform."""
        )

        await self.memory.remember("ad_campaigns", result[:600], category="ads")
        await self.send_message("cmo", f"Ad Copy Ready: {result[:300]}", "report")
        return result

    # ── Visual Content Briefs ──────────────────────────────
    async def _visual_content_brief(self, description: str) -> str:
        """Create briefs for graphics, infographics, and video content."""
        result = await self.think(
            f"""Visual content brief task: {description}

Product: {settings.product_name}
Brand: Hacker aesthetic (dark theme, terminal green, cyberpunk vibes)

**1. Social Media Graphics**:

**Twitter/X Header**:
- Dimensions: 1500x500px
- Content: Product name, tagline, GitHub stars count, terminal aesthetic
- Colors: Dark background (#0d1117), green accents (#00ff41), white text

**GitHub Social Preview**:
- Dimensions: 1280x640px
- Content: Logo, tagline, key features (3 icons), terminal screenshot
- Must look good at thumbnail size

**2. Infographic Brief**:
- Topic: "How AI Pentesting Works" (vertical, Instagram/Pinterest friendly)
- Sections: Problem → AI Approach → Features → Results → Try It
- Style: Dark mode, neon accents, iconography
- Dimensions: 1080x1920px

**3. Demo GIF** (for README/Twitter):
- Duration: 15-30 seconds
- Show: Type a prompt → AI thinks → Pentesting output
- Terminal recording (asciinema or ttygif)
- Add text overlay explaining what's happening

**4. Video Script** (60-second product demo):
- 0-5s: Hook — "What if AI could do your recon?"
- 5-15s: Problem — Manual pentesting is slow and tedious
- 15-35s: Demo — Show {settings.product_name} in action
- 35-50s: Features — 3 key capabilities
- 50-60s: CTA — Star on GitHub, join Discord

**5. Slide Deck** (for presentations/pitches):
- 10 slides: Problem, Solution, Demo, Features, Architecture, Traction, Team, Roadmap, CTA
- Design: Dark mode, minimal text, big visuals

For each brief, describe exactly what the visual should contain, dimensions, colors, and text."""
        )

        await self.memory.remember("visual_briefs", result[:400], category="visual")
        return result

    # ── Growth Experiments ─────────────────────────────────
    async def _growth_experiment(self, description: str) -> str:
        """Design growth hacking experiments and viral mechanics."""
        prev_experiments = await self.memory.recall("growth_experiments", "growth")

        result = await self.think(
            f"""Growth experiment task: {description}

Previous Experiments: {prev_experiments or 'None yet.'}
Product: {settings.product_name} (open-source, GitHub-based)
Goal: GitHub stars, Discord members, active users

**1. Viral Loop Experiments**:

**Experiment A: "Star to Unlock"**
- Hypothesis: Gating a premium feature behind GitHub stars increases stars
- Mechanic: Star the repo → get access to advanced prompts pack
- Measurement: Stars/day before vs after
- Effort: Medium

**Experiment B: "Share Your Results"**
- Hypothesis: Users sharing their pentesting results drives organic growth
- Mechanic: Output includes "Generated by {settings.product_name}" with link
- Measurement: Referral traffic from shared results
- Effort: Low

**Experiment C: "CTF Challenge"**
- Hypothesis: Creating a {settings.product_name}-powered CTF challenge attracts security community
- Mechanic: Host a challenge, require {settings.product_name} to solve it
- Measurement: New users from CTF
- Effort: High

**2. Growth Hack Ideas** (rank by expected impact / effort):
- [ ] GitHub "Awesome" lists — get listed on awesome-hacking, awesome-security
- [ ] Show HN post with great storytelling
- [ ] Tool comparison table (us vs competitors)
- [ ] Free security scanning for open-source projects
- [ ] "Hacktoberfest" contributions welcome
- [ ] Discord verification → GitHub star bonus
- [ ] Referral system (invite 3 friends → attribution in CONTRIBUTORS.md)

**3. Experiment Template**:
| Field | Value |
|-------|-------|
| Hypothesis | [If we X, then Y will happen] |
| Metric | [Primary KPI] |
| Duration | [7/14/30 days] |
| Success Criteria | [+X% improvement] |
| Effort | [S/M/L] |
| Status | [Planned/Running/Done] |

Design 3 experiments with full details. Prioritize by impact/effort ratio."""
        )

        await self.memory.remember("growth_experiments", result[:600], category="growth")
        await self.send_message("cmo", f"Growth Experiments: {result[:300]}", "report")
        return result

    # ── Content Analytics ──────────────────────────────────
    async def _content_analytics(self, description: str) -> str:
        """Analyse content performance and report metrics."""
        recent_posts = await self.memory.recall("recent_posts", "social")
        blog_data = await self.memory.recall(f"blog_{datetime.now(timezone.utc).strftime('%Y%m%d')}", "blog")

        result = await self.think(
            f"""Content analytics task: {description}

Recent Social Posts: {recent_posts[:300] if recent_posts else 'No tracking data.'}
Blog Content: {blog_data[:200] if blog_data else 'No blog data.'}

**1. Content Performance Dashboard**:

| Metric | This Week | Last Week | Trend |
|--------|-----------|-----------|-------|
| Social media posts created | [count] | [count] | ↑/↓ |
| Blog posts published | [count] | [count] | ↑/↓ |
| Community engagements | [count] | [count] | ↑/↓ |
| Email campaigns sent | [count] | [count] | ↑/↓ |

**2. Platform Performance**:
- Twitter/X: Impressions, engagement rate, follower growth
- Reddit: Upvotes, comments, traffic referral
- LinkedIn: Views, reactions, follower growth
- GitHub README: Stars this week, forks, contributor growth
- Discord: New members, message activity

**3. Top Performing Content**:
- What got the most engagement?
- What drove the most GitHub stars?
- What brought the most Discord joins?
- Common themes in top content

**4. Underperforming Content**:
- What didn't work?
- Why? (timing, platform, message, audience)
- Learnings to apply

**5. Recommendations**:
- Double down on: [what's working]
- Stop doing: [what's not working]
- Try next: [new experiment]
- Content calendar adjustment

**6. KPI Tracking**:
- GitHub stars: [current] → [target]
- Discord members: [current] → [target]
- Website traffic: [current] → [target]
- Email subscribers: [current] → [target]

Provide analysis and specific actionable recommendations."""
        )

        await self.memory.remember("content_performance", result[:600], category="analytics")
        await self.send_message("cmo", f"Analytics Report: {result[:300]}", "report")
        return result

    # ── Competitive Content ────────────────────────────────
    async def _competitive_content(self, description: str) -> str:
        """Analyse competitor content and create counter-content."""
        result = await self.think(
            f"""Competitive content analysis task: {description}

Product: {settings.product_name} — AI pentesting chatbot

**1. Competitor Content Audit**:

Identify top 5 competitors in AI security tools space:
- What content are they creating?
- Which platforms are they active on?
- What messaging/positioning do they use?
- What content gets them the most engagement?

**2. Content Gap Analysis**:
| Topic | Competitor Coverage | Our Coverage | Opportunity |
|-------|-------------------|--------------|-------------|
| AI pentesting tutorials | [Y/N] | [Y/N] | [High/Med/Low] |
| Security tool comparisons | [Y/N] | [Y/N] | [High/Med/Low] |
| CTF writeups with AI | [Y/N] | [Y/N] | [High/Med/Low] |
| Beginner security guides | [Y/N] | [Y/N] | [High/Med/Low] |

**3. Counter-Content Strategy**:
For each gap found:
- Content piece to create
- Platform to publish on
- How it differentiates from competitor content
- Expected impact

**4. "10x Content" Opportunities**:
- What topic can we cover 10x better than anyone else?
- What unique perspective do we bring?
- What data/experience only we have?

**5. Positioning Differences to Emphasize**:
- Open-source (vs closed/paid tools)
- AI-native (vs bolted-on AI)
- Community-driven (vs corporate)
- Hacker-friendly (vs enterprise-focused)

Write 2 specific content pieces targeting the biggest gaps found."""
        )

        await self.memory.remember("competitive_content", result[:400], category="competitive")
        await self.send_message("cmo", f"Competitive Analysis: {result[:300]}", "report")
        return result

    # ── PR & Media ─────────────────────────────────────────
    async def _pr_media(self, description: str) -> str:
        """Draft press releases, media pitches, and journalist outreach."""
        result = await self.think(
            f"""PR and media task: {description}

Product: {settings.product_name}

**1. Press Release Template**:
```
FOR IMMEDIATE RELEASE

[Headline — newsworthy, not promotional]

[City, Date] — {settings.company_name} today announced [what's new].

[Paragraph 1: What and why it matters]
[Paragraph 2: Key features/details]
[Paragraph 3: Quote from founder]
[Paragraph 4: Availability and how to get it]

About {settings.company_name}:
[2-3 sentences about the company]

Contact: [email]
```

**2. Media Pitch Email**:
```
Subject: [Newsworthy angle, not product name]

Hi [journalist name],

[1 sentence connecting to their recent coverage]

[2 sentences on what's new and why their readers would care]

[1 sentence offering exclusive angle/demo/interview]

[Link to more info]

Thanks,
[Name]
```

**3. Target Publications**:
- **Tech**: TechCrunch, The Verge, Ars Technica
- **Security**: BleepingComputer, The Hacker News (THN), SecurityWeek
- **Dev**: Dev.to, Hacker Noon, InfoQ
- **Open Source**: FOSS blogs, OpenSource.com

**4. PR Calendar**:
- Launch announcement
- Major feature releases
- Milestone celebrations (100 stars, 1000 users)
- Security advisories (builds credibility)

Write one complete press release and one personalized media pitch."""
        )

        await self.send_message("cmo", f"PR Content: {result[:300]}", "report")
        return result

    # ── Event Marketing ────────────────────────────────────
    async def _event_marketing(self, description: str) -> str:
        """Create marketing content for conferences, webinars, CTFs."""
        result = await self.think(
            f"""Event marketing task: {description}

Product: {settings.product_name}

**1. Conference Talk Proposal** (CFP submission):
- Title: [3 options]
- Abstract (200 words): [compelling, specific, outcome-focused]
- Target conferences: DEF CON, Black Hat, BSides, OWASP AppSec, PyCon
- Speaker bio

**2. Webinar Plan**:
- Title: "Live Demo: AI-Powered Pentesting with {settings.product_name}"
- Duration: 45 min + 15 min Q&A
- Outline:
  1. Problem (5 min)
  2. Live demo (20 min)
  3. Architecture deep-dive (10 min)
  4. Q&A (15 min)
- Registration page copy
- Promotional tweets (3)
- Email invitation

**3. CTF Event**:
- Host a {settings.product_name}-themed CTF challenge
- 3-5 challenges of increasing difficulty
- Theme: "Can you outsmart the AI?"
- Prizes: Swag, Discord role, CONTRIBUTORS.md mention
- Promotional content for CTF

**4. Hackathon Presence**:
- Sponsor challenge: "Best use of {settings.product_name}"
- Mentoring offer
- Swag/prizes
- Post-hackathon content (winners, projects)

**5. Pre/Post Event Content**:
- Announcement posts (social media)
- Countdown content (3 days, 1 day, today)
- Live coverage (tweets, photos)
- Post-event recap blog
- Slide deck sharing

Write complete content for the highest-priority event item."""
        )

        await self.memory.remember("event_marketing", result[:400], category="events")
        await self.send_message("cmo", f"Event Content: {result[:300]}", "report")
        return result

    # ── Content Repurposing ────────────────────────────────
    async def _repurpose_content(self, description: str) -> str:
        """Turn one piece of content into multiple formats for different channels."""
        recent_blog = await self.memory.recall(f"blog_{datetime.now(timezone.utc).strftime('%Y%m%d')}", "blog")

        result = await self.think(
            f"""Content repurposing task: {description}

Source Content: {recent_blog[:400] if recent_blog else 'Use the latest blog post or product update.'}

**Repurposing Framework** — Turn 1 piece into 10+:

From a single blog post, create:

**1. Twitter/X Thread** (5-7 tweets):
- Tweet 1: Hook with key insight
- Tweets 2-5: Main points, one per tweet
- Tweet 6: Summary + CTA
- Tweet 7: "If you enjoyed this, follow for more [topic]"

**2. LinkedIn Post**:
- Hook (first 2 lines before "see more")
- 3 key takeaways from the blog
- Personal angle/opinion
- Question to drive comments

**3. Reddit Post**:
- Title: question or insight format
- Body: condensed, community-appropriate version
- No promotional language

**4. Email Newsletter Snippet**:
- 3-sentence summary
- "Read the full post" CTA

**5. Instagram/Twitter Carousel** (brief):
- Slide 1: Hook/title
- Slides 2-5: Key points (one per slide)
- Slide 6: CTA

**6. YouTube Short / TikTok Script** (60 sec):
- Hook (3 sec)
- Key insight (40 sec)
- CTA (5 sec)

**7. Quote Graphics** (text for 3 images):
- Pull best quotes/stats from the content
- Format as shareable quote cards

**8. Hacker News Comment**:
- If related thread exists, write a value-add comment referencing the content

Write ALL the repurposed content pieces — ready to publish."""
        )

        await self.send_message("cmo", f"Repurposed Content: {result[:300]}", "report")
        return result

    # ── Brand Voice Guide ──────────────────────────────────
    async def _brand_voice_guide(self, description: str) -> str:
        """Define and maintain consistent brand voice across all content."""
        result = await self.think(
            f"""Brand voice task: {description}

Product: {settings.product_name}
Company: {settings.company_name}

**Brand Voice Guide**:

**1. Voice Attributes**:
- **Technical**: We know our stuff. Use proper terminology, don't dumb it down.
- **Approachable**: Not gatekeeping. Welcome beginners and experts alike.
- **Hacker-Friendly**: Speak the community's language. We're builders, not suits.
- **Honest**: No hype. Acknowledge limitations. Underpromise, overdeliver.
- **Exciting**: We're building something genuinely cool. Let that energy show.

**2. Tone by Channel**:
| Channel | Formality | Humor | Technical Depth |
|---------|-----------|-------|-----------------|
| Twitter/X | Casual | Yes | Medium |
| LinkedIn | Professional | Light | Medium-High |
| Reddit | Casual | Community-appropriate | High |
| Blog | Professional-casual | Occasional | High |
| Email | Friendly | Light | Medium |
| GitHub | Technical | Minimal | Very High |
| Discord | Very casual | Yes | Varies |

**3. Do's and Don'ts**:
DO:
- Use "we" (community) and "you" (direct)
- Show, don't tell (demos > claims)
- Reference real tools, techniques, CVEs
- Celebrate the community
- Be transparent about what works and what doesn't

DON'T:
- Use corporate jargon ("synergy", "leverage", "paradigm")
- Overhype ("revolutionary", "game-changing")
- Talk down to beginners
- Be defensive about criticism
- Use all caps for emphasis (except in casual Discord)

**4. Terminology Guide**:
- Say "pentesting" not "penetration testing" (in casual contexts)
- Say "security researchers" not "hackers" (in public/professional)
- Say "open-source" not "free" (emphasize freedom, not price)
- Say "AI-powered" not "AI-driven" (more active)

**5. Example Rewrites**:
Bad: "Our revolutionary AI-driven platform leverages cutting-edge technology..."
Good: "We built an AI that does your recon while you grab coffee."

Provide the complete brand voice guide as a reference document."""
        )

        await self.memory.remember("brand_voice", result[:600], category="brand")
        await self.send_message("cmo", f"Brand Voice Guide: {result[:300]}", "report")
        return result

    # ── Intelligence Gathering ─────────────────────────────
    async def _get_inbox_summary(self) -> str:
        msgs = await self.read_messages()
        if not msgs:
            return "No new messages."
        return "\n".join(
            f"- {m.get('from_agent', '?')} ({m.get('channel', '?')}): {m.get('content', '')[:100]}"
            for m in msgs[:10]
        )

    # ── Enhanced Report ────────────────────────────────────
    async def generate_report(self) -> str:
        """Marketing generates a content & distribution executive report."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]

        perf = await self.memory.recall("content_performance", "analytics")
        social = await self.memory.recall("recent_posts", "social")
        growth = await self.memory.recall("growth_experiments", "growth")

        report = await self.think(
            f"""Generate the Marketing daily report.

## Marketing Tasks Today
{json.dumps(today_tasks, indent=2) if today_tasks else 'No marketing tasks today.'}

## Content Performance
{perf[:300] if perf else 'No analytics yet.'}

## Social Media Activity
{social[:200] if social else 'No posts tracked yet.'}

## Growth Experiments
{growth[:200] if growth else 'No experiments running.'}

Write a concise marketing report:
1. Content produced today (posts, articles, emails)
2. Platforms covered
3. Community engagement score: 🟢 Active / 🟡 Moderate / 🔴 Low
4. Top performing content (or best candidate)
5. Growth experiment status
6. Content pipeline (what's in progress)
7. Tomorrow's priorities (top 3)
8. CMO attention needed (if any)

Under 250 words. Specific and results-oriented."""
        )

        await state_manager.save_daily_report(self.agent_id, report)
        return f"**Marketing Content & Distribution Report**\n{report}"
