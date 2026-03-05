"""Sales Team Agent — the revenue & partnerships engine. Handles outreach, lead gen,
partnerships, enterprise sales, community BD, conference networking, influencer deals,
pricing strategy, pipeline management, and drives every business relationship."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.state_manager import state_manager
from config import settings


class SalesAgent(BaseAgent):
    agent_id = "sales"
    role = "Sales Team Lead"
    description = (
        "Handles outreach, partnerships, lead generation, business development, "
        "enterprise sales, pricing, and pipeline management."
    )
    pixel_sprite = "sprite-sales"

    def __init__(self):
        super().__init__()
        self.position = {"x": 200, "y": 250}

    def get_system_prompt(self) -> str:
        return f"""You are the Sales Team Lead at {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You are the deal-maker, the relationship builder, the revenue engine.
Every partnership, sponsorship, enterprise lead, and business opportunity flows through you.

Your responsibilities:
1. **Partner Identification** — Research and identify cybersecurity companies, platforms, and communities for partnerships.
2. **Outreach & Cold Email** — Write compelling, personalized outreach emails that get replies (not spam).
3. **Enterprise Leads** — Identify companies that could use {settings.product_name} at scale (security teams, MSSPs, training orgs).
4. **Partnership Proposals** — Draft formal partnership decks: value prop, collaboration models, mutual benefits.
5. **Influencer Deals** — Negotiate sponsorships, reviews, collaborations with security YouTubers/bloggers.
6. **Conference & Events** — Research events (DEF CON, Black Hat, BSides), plan presence, network.
7. **Pricing & Monetization** — Develop pricing strategy for freemium/premium/enterprise tiers.
8. **Pipeline Management** — Track all leads, deals, and relationships through stages (cold → warm → hot → closed).
9. **Competitive Intelligence** — Track competitor pricing, partnerships, and positioning.
10. **Community BD** — Build relationships with CTF platforms, bug bounty programs, security training sites.
11. **Sponsorship Strategy** — Identify and pursue sponsorship opportunities (podcasts, events, newsletters, repos).
12. **Referral Program** — Design and manage referral/affiliate programs.
13. **Customer Success** — Onboard early users/partners and ensure they succeed.
14. **Revenue Reporting** — Track revenue metrics, forecasts, and report to CEO.
15. **Strategic Alliances** — Build long-term alliances with complementary tools and platforms.
16. **Market Expansion** — Identify new markets, verticals, and use cases for the product.

Current stage: Zero users, open-source freemium model.
Focus: Partnerships, community BD, influencer collabs, and building the early user base.
Revenue model: Open-source core → Premium features → Enterprise licenses.

When planning tasks, output a JSON array with keys: type, description, priority (1-5).
Types: outreach, partnership, enterprise, influencer, conference, pricing, pipeline,
competitive, community_bd, sponsorship, referral, customer_success, revenue, alliance,
market_expansion, cold_email."""

    # ── Planning ───────────────────────────────────────────
    async def plan_day(self) -> list[dict]:
        inbox = await self._get_inbox_summary()
        my_memories = await self.memory.get_context_summary()
        pipeline = await self.memory.recall("sales_pipeline", "pipeline")
        prev_outreach = await self.memory.recall("outreach_status", "outreach")

        context = f"""## Inbox
{inbox}

## Sales Pipeline
{pipeline or 'No pipeline data yet — start building it.'}

## Previous Outreach
{prev_outreach or 'No outreach tracked yet.'}

## Sales Memory
{my_memories}"""

        result = await self.think_json(
            f"""Plan sales and business development tasks for this cycle.

{context}

ALWAYS include these daily activities:
1. Pipeline check — update lead statuses, follow up on warm leads
2. Outreach — at least 1-2 new outreach messages (partners, influencers, or enterprise)
3. One strategic task — pricing, partnership proposal, or market research

Then add 2-3 tasks based on current pipeline and priorities.

Balance prospecting (new leads) with nurturing (existing relationships).

Return a JSON array of 4-6 tasks with keys: type, description, priority (1-5).""",
        )

        if isinstance(result, list):
            return result
        return [
            {"type": "pipeline", "description": "Review and update sales pipeline — follow up on warm leads", "priority": 1},
            {"type": "outreach", "description": "Research and reach out to cybersecurity influencers", "priority": 1},
            {"type": "partnership", "description": "Draft partnership proposal for security platforms", "priority": 2},
        ]

    # ── Task Execution ─────────────────────────────────────
    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "outreach")
        description = task.get("description", "")

        handlers = {
            "outreach": self._do_outreach,
            "cold_email": self._write_cold_emails,
            "partnership": self._partnership_proposal,
            "enterprise": self._enterprise_sales,
            "influencer": self._influencer_deals,
            "conference": self._conference_strategy,
            "pricing": self._pricing_strategy,
            "pipeline": self._manage_pipeline,
            "competitive": self._competitive_intel,
            "community_bd": self._community_bd,
            "sponsorship": self._sponsorship_strategy,
            "referral": self._referral_program,
            "customer_success": self._customer_success,
            "revenue": self._revenue_reporting,
            "alliance": self._strategic_alliance,
            "market_expansion": self._market_expansion,
        }

        handler = handlers.get(task_type)
        if handler:
            return await handler(description)

        # Generic sales task
        result = await self.think(
            f"Execute this sales/BD task:\n{description}\n\n"
            "Provide specific, actionable output. If it involves outreach, write the real messages."
        )

        if task_type in ("partnership", "enterprise", "alliance"):
            await self.send_message("ceo", f"BD Opportunity: {result[:300]}", "business")

        return result

    # ── Outreach ───────────────────────────────────────────
    async def _do_outreach(self, description: str) -> str:
        """Research targets and craft outreach messages."""
        prev = await self.memory.recall("outreach_status", "outreach")

        result = await self.think(
            f"""Outreach task: {description}

Previous Outreach: {prev or 'Starting fresh.'}
Product: {settings.product_name} — AI pentesting chatbot (open-source)

**1. Target Research**:

**Category A: Security Tool Companies** (partnership):
- Burp Suite, OWASP ZAP, Nmap, Metasploit — integration partners
- HackTheBox, TryHackMe — training platform integration
- Snyk, Semgrep — security tool ecosystem

**Category B: Security Content Creators** (exposure):
- YouTube: John Hammond, NetworkChuck, The Cyber Mentor, IppSec
- Podcasts: Darknet Diaries, Security Now
- Blogs: Hacker Noon security, Medium security writers

**Category C: Companies/Teams** (enterprise):
- Security consulting firms (100-500 employees)
- MSSPs (Managed Security Service Providers)
- University cybersecurity programs

**2. For Each Target**:
- Who they are and why they're a fit
- What we offer them (value prop specific to them)
- What we want from them
- Outreach channel (email, DM, LinkedIn)
- Priority: 🔴 High / 🟡 Medium / 🟢 Nice-to-have

**3. Outreach Messages** (3 different targets):
Write personalized, ready-to-send messages:
- Personalized hook (reference their recent work)
- Clear value proposition (what's in it for them)
- Low-barrier CTA (not "buy now" — more like "check it out" or "quick chat?")
- Professional but not corporate

Research 5 targets and write 3 complete outreach messages."""
        )

        await self.memory.remember("outreach_status", result[:600], category="outreach")
        return result

    # ── Cold Email Templates ───────────────────────────────
    async def _write_cold_emails(self, description: str) -> str:
        """Write high-converting cold email sequences."""
        result = await self.think(
            f"""Cold email task: {description}

Product: {settings.product_name}
Stage: Open-source, looking for early adopters and partners

**Cold Email Framework** — The 3-email sequence that gets replies:

**Email 1: The Opener** (Day 1)
- Subject line: [3 A/B options — curiosity-driven, not clickbait]
  - Option A: "Quick thought about [their company]'s security workflow"
  - Option B: "[Their name] — fellow security builder here"
  - Option C: "[Specific thing they did] caught my eye"
- Body structure:
  - Line 1: Personalized hook (reference their work, NOT "I hope this finds you well")
  - Line 2: Your credibility in 1 sentence
  - Line 3: What you built and why they'd care (2 sentences max)
  - Line 4: Specific, low-commitment CTA
  - Line 5: Sign-off
- Total: 4-6 sentences. No walls of text.

**Email 2: The Follow-Up** (Day 3-4)
- Subject: Re: [same thread]
- Body: "Hey [name], wanted to bump this. [One new piece of info or social proof]. [Same CTA]."
- 2-3 sentences max.

**Email 3: The Breakup** (Day 7-8)
- Subject: Re: [same thread]
- Body: "Hi [name], I'll assume the timing isn't right. If [product] ever comes up, here's the link: [URL]. No hard feelings — would love to connect down the road."

**Email Templates for Each Target Type**:

**For Security Tool Companies** (partnership):
[Write complete 3-email sequence]

**For Influencers** (collaboration):
[Write complete 3-email sequence]

**For Enterprise Security Teams** (user acquisition):
[Write complete 3-email sequence]

Rules:
- NEVER use "I hope this finds you well"
- NEVER send identical emails to different people
- Always personalize the first line
- Keep under 100 words per email
- One CTA per email
- Plain text (no HTML, no images in cold email)"""
        )

        await self.memory.remember("cold_email_templates", result[:600], category="email")
        return result

    # ── Partnership Proposals ──────────────────────────────
    async def _partnership_proposal(self, description: str) -> str:
        """Draft formal partnership proposals and collaboration frameworks."""
        result = await self.think(
            f"""Partnership proposal task: {description}

Product: {settings.product_name}
GitHub: {settings.product_github_url}

**Partnership Proposal Framework**:

**1. Executive Summary** (1 paragraph):
- Who we are, what we've built, why partner with us

**2. Partnership Models** (offer multiple options):

**Model A: Integration Partnership** 🔌
- Integrate {settings.product_name} with their platform
- Mutual API access
- Co-branded feature
- Revenue share on premium features
- Joint marketing

**Model B: Content Partnership** 📝
- They create content featuring our tool
- We provide exclusive access/features
- Cross-promotion to both audiences
- Affiliate revenue share

**Model C: Distribution Partnership** 📦
- They bundle/recommend our tool
- We provide white-label option
- Volume licensing discount
- Joint customer support

**Model D: Training Partnership** 🎓
- Include {settings.product_name} in their training/courses
- Educational license (free/discounted)
- We provide curriculum support
- Joint certification

**3. Value Proposition** (specific to partner type):

**For HackTheBox/TryHackMe**:
- Add AI-assisted pentesting to their platform
- New training module category
- Differentiation from competitors
- Shared user growth

**For Security Tool Companies (Burp, ZAP)**:
- AI layer on top of their scanning
- Plugin integration
- Expanded capabilities without R&D cost
- Mutual referral traffic

**For Enterprise (consulting firms, MSSPs)**:
- Automate junior analyst tasks
- Faster report generation
- Scale security assessments
- White-label option

**4. Terms Template**:
- Partnership duration
- Responsibilities matrix
- Revenue share structure
- IP ownership
- Marketing commitments
- Success metrics
- Exit clause

Write 2 complete partnership proposals for specific targets."""
        )

        await self.memory.remember("partnership_proposals", result[:600], category="partnerships")
        await self.send_message("ceo", f"Partnership Proposal: {result[:400]}", "business")
        return result

    # ── Enterprise Sales ───────────────────────────────────
    async def _enterprise_sales(self, description: str) -> str:
        """Identify and pursue enterprise sales opportunities."""
        result = await self.think(
            f"""Enterprise sales task: {description}

Product: {settings.product_name}
Model: Open-source core → Premium → Enterprise

**1. Ideal Customer Profile (ICP)**:

**Tier 1: Perfect Fit**
- Security consulting firms (50-500 employees)
- MSSPs with pentest teams
- Large companies with in-house security teams (>10 people)
- Use case: Augment human pentesters with AI

**Tier 2: Good Fit**
- DevSecOps teams at tech companies
- University cybersecurity programs
- Government security agencies
- Use case: Training, automation, research

**Tier 3: Emerging Fit**
- Bug bounty platforms
- CTF competition organizers
- Security bootcamps
- Use case: Education, practice, gamification

**2. Enterprise Features Wishlist** (what to build for enterprise):
- [ ] SSO/SAML authentication
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Custom model/API support
- [ ] On-premise deployment
- [ ] SLA with support
- [ ] Compliance reports
- [ ] Team management dashboard
- [ ] Custom integrations

**3. Enterprise Sales Process**:
```
Identify → Research → Outreach → Discovery Call → Demo → 
Proposal → Negotiation → Close → Onboard
```

**4. Discovery Call Script**:
- Opening (build rapport): 2 min
- Their current workflow: 5 min
- Pain points: 5 min
- Demo (tailored to their needs): 10 min
- Q&A: 5 min
- Next steps: 3 min

**5. Objection Handling**:
| Objection | Response |
|-----------|----------|
| "It's open source, why pay?" | Enterprise features, SLA, support, customization |
| "Security concerns with AI" | On-prem option, audit logs, no data sharing |
| "We already have tools" | Augments, doesn't replace — show integration |
| "Budget constraints" | Start with free tier, prove ROI, then upgrade |
| "Not mature enough" | Early adopter pricing, influence roadmap |

**6. Target List** (5 specific companies):
For each: company name, why they fit, who to contact, outreach approach

Research and provide actionable enterprise targets."""
        )

        await self.memory.remember("enterprise_leads", result[:600], category="enterprise")
        await self.send_message("ceo", f"Enterprise BD: {result[:400]}", "business")
        return result

    # ── Influencer Deals ───────────────────────────────────
    async def _influencer_deals(self, description: str) -> str:
        """Negotiate and structure influencer collaborations."""
        result = await self.think(
            f"""Influencer deals task: {description}

Product: {settings.product_name}
Budget: Bootstrap (minimize cash, maximize creative deals)

**1. Influencer Tier System**:

**Tier A: Mega** (100K+ subscribers):
- John Hammond, NetworkChuck, The Cyber Mentor
- Deal: Free product + affiliate revenue share
- Content: Dedicated video/review
- Expected reach: 50K-200K views

**Tier B: Mid** (10K-100K subscribers):
- Security-focused YouTubers, bloggers
- Deal: Free product + feature in our community
- Content: Mention in video or dedicated segment
- Expected reach: 5K-50K views

**Tier C: Micro** (1K-10K followers):
- CTF players, security students, up-and-comers
- Deal: Free product + CONTRIBUTORS.md credit + feature on our socials
- Content: Tweet/thread, short review
- Expected reach: 1K-5K impressions

**2. Deal Structures** (no budget? no problem):

**Option A: Revenue Share**
- Influencer gets unique referral link
- 20% of any premium conversions from their link
- Tracked via affiliate system

**Option B: Feature Exchange**
- They review us → we feature them in our community
- Cross-promotion to both audiences
- Joint live stream/demo

**Option C: Content Swap**
- They create content about us
- We create content featuring their channel
- Win-win exposure

**Option D: Early Access**
- Exclusive early access to new features
- They get to "break" it first (appealing to hackers)
- Their feedback shapes the product

**3. Approach Strategy**:
For each tier, write:
- Specific DM/email template
- What to offer
- What to ask for
- Follow-up cadence
- When to walk away

**4. Negotiation Principles**:
- Always lead with what THEY get
- Never pay upfront for unproven influencers
- Start with smallest commitment
- Scale up based on results

Write 3 complete influencer deal proposals."""
        )

        await self.memory.remember("influencer_deals", result[:600], category="influencer")
        await self.send_message("cmo", f"Influencer Deals: {result[:300]}", "report")
        return result

    # ── Conference Strategy ────────────────────────────────
    async def _conference_strategy(self, description: str) -> str:
        """Research and plan conference presence and networking."""
        result = await self.think(
            f"""Conference strategy task: {description}

Product: {settings.product_name}
Budget: Bootstrap — focus on free/low-cost opportunities

**1. Target Conferences** (2026):

**Tier A: Must-Attend**
| Conference | When | Where | Cost | Why |
|-----------|------|-------|------|-----|
| DEF CON | Aug | Las Vegas | Free/cheap | Largest hacking conference |
| Black Hat USA | Aug | Las Vegas | $$$$ | Enterprise buyers |
| BSides (various) | Year-round | Various | Free | Community, grassroots |
| OWASP Global | Various | Various | Moderate | AppSec community |

**Tier B: Good Opportunities**
| Conference | When | Where | Cost | Why |
|-----------|------|-------|------|-----|
| Wild West Hackin' Fest | Oct | Deadwood, SD | Moderate | Great community |
| PyCon | May | Various | Moderate | Python community (our stack) |
| RSA Conference | Apr | San Francisco | $$$$ | Enterprise, media |

**Tier C: Online/Free**
- Virtual security meetups
- Discord-based events
- Twitter Spaces / LinkedIn Live
- Webinars (host our own)

**2. Conference Playbook** (for each event):

**Pre-Conference** (2-4 weeks before):
- Research attendees and speakers
- Schedule meetings in advance
- Prepare elevator pitch (30 seconds)
- Print business cards / prepare digital contact exchange
- Prepare demo on laptop (offline-capable)
- Social media: "Who's going to [conference]?"

**During Conference**:
- Attend relevant talks (take notes)
- Network in hallways (this is where deals happen)
- Live demo to interested people
- Collect contacts (name, company, interest)
- Post on social media (live coverage)
- Host an informal meetup/dinner

**Post-Conference** (within 48 hours):
- Send follow-up emails to ALL contacts
- Connect on LinkedIn with personal note
- Share takeaways on blog/social
- Update pipeline with new leads
- Debrief with team

**3. Speaking Opportunities** (free marketing):
- CFP (Call for Papers) submissions
- Lightning talks
- Demo/tool showcase slots
- Panel discussions

**4. Budget-Friendly Presence**:
- Volunteer (free ticket + networking)
- Speaker (free ticket + exposure)
- Sponsor small events ($100-500)
- Community booth at BSides (often free)

Research specific 2026 events and create an events calendar."""
        )

        await self.memory.remember("conference_strategy", result[:600], category="events")
        await self.send_message("ceo", f"Conference Plan: {result[:300]}", "business")
        return result

    # ── Pricing Strategy ───────────────────────────────────
    async def _pricing_strategy(self, description: str) -> str:
        """Develop pricing tiers, monetization strategy, and revenue model."""
        prev_pricing = await self.memory.recall("pricing_model", "pricing")

        result = await self.think(
            f"""Pricing strategy task: {description}

Previous Pricing Work: {prev_pricing or 'Starting fresh.'}
Product: {settings.product_name}
Model: Open-source core with premium tiers

**1. Pricing Tiers**:

**Free (Community Edition)** — Always free, open-source:
- Core AI pentesting features
- Community support (Discord)
- Standard models (GPT-3.5, Ollama)
- Personal use only
- GitHub: `hackbot` (MIT license)

**Pro ($19/mo or $190/yr)** — For individual security pros:
- Everything in Free
- Premium models (GPT-4, Claude)
- Advanced scanning techniques
- Priority support (Discord role)
- Custom prompt library
- Export reports (PDF, JSON)
- Cloud dashboard

**Team ($49/user/mo)** — For security teams:
- Everything in Pro
- Team management dashboard
- Shared prompt library
- Collaborative scans
- Audit logging
- SSO integration
- Priority email support

**Enterprise (Custom pricing)** — For large orgs:
- Everything in Team
- On-premise deployment
- Custom model integration
- Dedicated support engineer
- SLA (99.9% uptime)
- Custom integrations
- Compliance features
- Training and onboarding

**2. Pricing Psychology**:
- Anchor with Enterprise (makes Pro seem cheap)
- Yearly plan saves 2 months (incentivize annual)
- Free tier is generous (builds community, reduces friction)
- "Most Popular" badge on Pro

**3. Monetization Timeline**:
- Phase 1 (now): 100% free, build community
- Phase 2 (500+ stars): Launch Pro tier, early adopter discount (50% off)
- Phase 3 (2000+ stars): Launch Team tier
- Phase 4 (5000+ stars): Enterprise outreach

**4. Revenue Projections** (conservative):
| Milestone | Free Users | Pro | Team | MRR |
|-----------|-----------|-----|------|-----|
| Month 6 | 500 | 10 | 0 | $190 |
| Month 12 | 2,000 | 50 | 5 | $2,200 |
| Month 18 | 5,000 | 150 | 20 | $5,830 |
| Month 24 | 10,000 | 400 | 50 | $10,110 |

**5. Competitive Pricing Analysis**:
- Compare to similar tools (Burp Pro, Snyk, etc.)
- Why our pricing makes sense
- Where we undercut vs premium position

Produce the complete pricing page copy and strategy doc."""
        )

        await self.memory.remember("pricing_model", result[:600], category="pricing")
        await self.send_message("ceo", f"Pricing Strategy: {result[:400]}", "business")
        return result

    # ── Pipeline Management ────────────────────────────────
    async def _manage_pipeline(self, description: str) -> str:
        """Track and manage the sales pipeline — leads, deals, follow-ups."""
        prev_pipeline = await self.memory.recall("sales_pipeline", "pipeline")

        result = await self.think(
            f"""Pipeline management task: {description}

Current Pipeline: {prev_pipeline or 'Starting fresh — build the pipeline.'}

**1. Pipeline Stages**:
```
Prospect → Contacted → Interested → Demo/Meeting → Proposal → Negotiation → Closed Won/Lost
```

**2. Pipeline Template**:

| Lead | Type | Stage | Last Contact | Next Action | Priority | Notes |
|------|------|-------|-------------|-------------|----------|-------|
| [Company/Person] | [Partner/Enterprise/Influencer] | [Stage] | [Date] | [Specific action] | [H/M/L] | [Context] |

**3. Pipeline Health Check**:
- How many leads in each stage?
- What's stuck? (>7 days without progress)
- What's hot? (high priority, recent activity)
- What's dead? (no response after 3 touches)
- Win rate: % of proposals that close

**4. Follow-Up Cadence**:
- Day 1: Initial outreach
- Day 3: First follow-up (if no response)
- Day 7: Second follow-up (new angle/info)
- Day 14: Breakup email
- Day 30: Re-engagement (if timing wasn't right)

**5. Weekly Pipeline Review**:
- New leads added this week
- Leads that advanced stages
- Leads that stalled or went cold
- Revenue forecast update
- Top 3 deals to focus on next week

**6. Pipeline Metrics**:
- Total leads: [count]
- Conversion rate per stage
- Average deal cycle time
- Pipeline value (weighted by stage probability)

Update the pipeline with current status and next actions for each lead.
If starting fresh, create an initial target list of 10 prospects."""
        )

        await self.memory.remember("sales_pipeline", result[:600], category="pipeline")
        return result

    # ── Competitive Intelligence ───────────────────────────
    async def _competitive_intel(self, description: str) -> str:
        """Track competitor pricing, deals, and market positioning."""
        result = await self.think(
            f"""Competitive intelligence task: {description}

Product: {settings.product_name} — AI pentesting chatbot

**1. Competitive Landscape**:

**Direct Competitors** (AI + Security):
| Competitor | Pricing | Users | Strengths | Weaknesses |
|-----------|---------|-------|-----------|------------|
| PentestGPT | ? | ? | [analysis] | [analysis] |
| HackerGPT | ? | ? | [analysis] | [analysis] |
| AutoPentest tools | ? | ? | [analysis] | [analysis] |

**Indirect Competitors** (traditional security tools):
| Tool | Pricing | Market Share | Threat Level |
|------|---------|-------------|-------------|
| Burp Suite Pro | $449/yr | High | Medium |
| Metasploit Pro | $15K/yr | High | Low |
| Nmap/ZAP | Free | Very High | Low |
| Snyk | Freemium | High | Low |

**2. Competitive Positioning Map**:
```
                    AI-Powered
                        ↑
        [PentestGPT]  |  [{settings.product_name}]
                        |
Free ←──────────────────┼──────────────────→ Expensive
                        |
        [Nmap/ZAP]     |  [Burp Suite Pro]
                        ↓
                    Traditional
```

**3. Win/Loss Analysis**:
- Why do people choose us? (open-source, AI-native, community)
- Why might they choose competitors? (maturity, features, enterprise support)
- How to counter each competitor's advantage

**4. Battlecards** (for each major competitor):
- Their pitch vs our pitch
- Their weakness to exploit
- Objection they'll raise about us
- Proof points in our favour

**5. Market Trends**:
- AI in cybersecurity market size and growth
- Key trends affecting our space
- Opportunities to position against

Create actionable battlecards for top 3 competitors."""
        )

        await self.memory.remember("competitive_intel", result[:600], category="competitive")
        await self.send_message("ceo", f"Competitive Intel: {result[:300]}", "business")
        return result

    # ── Community BD ───────────────────────────────────────
    async def _community_bd(self, description: str) -> str:
        """Build relationships with security communities and platforms."""
        result = await self.think(
            f"""Community business development task: {description}

Product: {settings.product_name}
Discord: {settings.product_discord_url}

**1. Target Communities** (security ecosystem):

**CTF Platforms**:
- HackTheBox — integration as training tool
- TryHackMe — course material partnership
- PicoCTF — educational partnership
- CTFtime — event sponsorship

**Bug Bounty Platforms**:
- HackerOne — featured tool integration
- Bugcrowd — researcher tool partnership
- Synack — enterprise integration

**Learning Platforms**:
- Cybrary — course integration
- SANS — tool in labs
- Offensive Security — complementary tool

**Community Hubs**:
- InfoSec Twitter/X community
- r/netsec, r/cybersecurity
- Security Discord servers
- Slack groups (various infosec)

**2. Community Partnership Models**:

**Free Tool Listing**:
- Get listed on "awesome" lists (awesome-hacking, awesome-security)
- Tool comparison sites
- Security tool directories

**Educational Partnership**:
- Provide free licenses for students
- Create courseware using {settings.product_name}
- Guest lectures and workshops

**Event Partnership**:
- Sponsor CTF challenges
- Provide prizes for security events
- Co-host webinars

**3. Community Outreach Plan**:
For each target community:
- Who's the point of contact?
- What value do we provide?
- What's the ask?
- Outreach message (ready to send)
- Follow-up plan

Research and write outreach for top 5 community targets."""
        )

        await self.memory.remember("community_bd", result[:600], category="community")
        await self.send_message("cxo", f"Community BD Plan: {result[:300]}", "report")
        return result

    # ── Sponsorship Strategy ───────────────────────────────
    async def _sponsorship_strategy(self, description: str) -> str:
        """Identify and pursue sponsorship opportunities."""
        result = await self.think(
            f"""Sponsorship strategy task: {description}

Product: {settings.product_name}
Budget: Bootstrap ($0-500/mo for sponsorships)

**1. Sponsorship Opportunities** (budget-friendly):

**Podcasts** ($50-200/episode):
| Podcast | Audience | Cost | Fit |
|---------|----------|------|-----|
| Darknet Diaries | 500K+ | Likely expensive | Perfect audience |
| Security Now | 200K+ | Expensive | Good fit |
| Smashing Security | 30K+ | Moderate | Good fit |
| Smaller infosec pods | 5-20K | $50-100 | Best ROI |

**Newsletters** ($25-100/issue):
- tl;dr sec (security newsletter)
- Risky Biz newsletter
- SANS newsbites
- Hacker News digest newsletters

**Open Source Sponsorship**:
- Sponsor maintainers of tools we depend on (goodwill + visibility)
- GitHub Sponsors badges
- OpenCollective contributions

**Event Sponsorship** ($100-500):
- BSides events (local, affordable)
- CTF competitions (prize sponsor)
- University security clubs
- Online hackathons

**2. Sponsorship ROI Calculator**:
| Opportunity | Cost | Expected Reach | Expected Conversions | CPA |
|------------|------|---------------|---------------------|-----|
| [Podcast X] | $100 | 5,000 | 50 stars | $2/star |
| [Newsletter Y] | $50 | 3,000 | 30 stars | $1.67/star |

**3. Sponsorship Message Template**:
"Hey [name], love [their content]. We built {settings.product_name} [1 sentence].
Would you be open to a [specific sponsorship type]? We can offer [what we give]."

Prioritize by ROI and produce 3 ready-to-send sponsorship inquiries."""
        )

        await self.memory.remember("sponsorships", result[:400], category="sponsorship")
        await self.send_message("ceo", f"Sponsorship Plan: {result[:300]}", "business")
        return result

    # ── Referral Program ───────────────────────────────────
    async def _referral_program(self, description: str) -> str:
        """Design and manage referral/affiliate programs."""
        result = await self.think(
            f"""Referral program task: {description}

Product: {settings.product_name}

**1. Referral Program Design**:

**User Referral** (peer-to-peer):
- Mechanic: Share unique link → friend signs up → both get reward
- Reward options:
  - Contributor credit in CONTRIBUTORS.md
  - Exclusive Discord role ("Ambassador")
  - Early access to features
  - Free month of Pro (when launched)
- Refer 3 → Bronze Ambassador
- Refer 10 → Silver Ambassador
- Refer 25 → Gold Ambassador
- Refer 50 → Founding Ambassador (permanent credit)

**Affiliate Program** (for influencers/bloggers):
- 20% revenue share on Pro/Team signups
- Unique tracking link
- Dashboard with stats (clicks, conversions, earnings)
- Monthly payouts (Stripe/PayPal)
- Minimum payout: $50

**2. Viral Mechanics**:
- "Powered by {settings.product_name}" in output
- Share results → get more credits
- Invite to Discord → unlock feature
- GitHub star → unlock feature
- Leaderboard of top referrers

**3. Program Tracking**:
| Metric | Target |
|--------|--------|
| Viral coefficient | >1.0 (each user brings >1 new user) |
| Referral conversion | >15% |
| Active referrers | 10% of user base |
| Revenue from referrals | 30% of total |

**4. Launch Plan**:
- Phase 1: Manual tracking (spreadsheet)
- Phase 2: Automated tracking (referral link system)
- Phase 3: Full dashboard with payouts

Design the complete referral program and write launch announcement copy."""
        )

        await self.memory.remember("referral_program", result[:400], category="referral")
        await self.send_message("cmo", f"Referral Program: {result[:300]}", "report")
        return result

    # ── Customer Success ───────────────────────────────────
    async def _customer_success(self, description: str) -> str:
        """Onboard and support early users and partners."""
        result = await self.think(
            f"""Customer success task: {description}

Product: {settings.product_name}
Stage: Early users, every user matters enormously

**1. Early User Onboarding**:

**Welcome Flow**:
1. User stars GitHub repo → automated thank you (GitHub Action)
2. User joins Discord → welcome DM with quick start guide
3. User first interaction → check-in after 24 hours
4. Day 7 → "How's it going?" survey
5. Day 30 → Testimonial request

**First-Time User Guide**:
- Step 1: Install/setup (< 5 minutes)
- Step 2: First successful scan (guided)
- Step 3: Try an advanced feature (suggest one)
- Step 4: Join community
- Step 5: Share feedback

**2. Support Tiers**:
- Community: Discord #help channel (response < 4 hours)
- Pro: Priority Discord + email (response < 2 hours)
- Enterprise: Dedicated contact (response < 30 min)

**3. User Feedback Collection**:
- In-app: Quick rating after each session
- Monthly: NPS survey (1-10 recommend)
- Quarterly: Deep interviews (30 min, 5 users)
- Always: Discord feedback channel

**4. Success Metrics Per User**:
- First use within 24 hours of signup
- 3+ sessions in first week
- Joined community (Discord/GitHub discussions)
- Shared or recommended (organic)
- Upgraded to paid (when available)

**5. Churn Prevention**:
- Monitor: Users who stop using (>14 days inactive)
- Trigger: Win-back email with new feature/update
- Offer: Personal help/walkthrough
- Learn: Exit survey if they leave

Provide the actual messages and templates for each touchpoint."""
        )

        await self.memory.remember("customer_success", result[:600], category="success")
        await self.send_message("cxo", f"Customer Success Plan: {result[:300]}", "report")
        return result

    # ── Revenue Reporting ──────────────────────────────────
    async def _revenue_reporting(self, description: str) -> str:
        """Track and report revenue metrics and forecasts."""
        pipeline = await self.memory.recall("sales_pipeline", "pipeline")
        pricing = await self.memory.recall("pricing_model", "pricing")

        result = await self.think(
            f"""Revenue reporting task: {description}

Pipeline: {pipeline[:300] if pipeline else 'No pipeline data.'}
Pricing: {pricing[:300] if pricing else 'No pricing model yet.'}

**1. Revenue Dashboard**:

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| MRR (Monthly Recurring Revenue) | $0 | $500 | Pre-revenue |
| Pipeline Value | $[X] | $[X] | [status] |
| Active Leads | [count] | 20 | [status] |
| Conversion Rate | [X]% | 5% | [status] |
| Average Deal Size | $[X] | $[X] | [status] |

**2. Revenue Forecast** (next 6 months):
| Month | Free Users | Pro | Team | Enterprise | MRR |
|-------|-----------|-----|------|-----------|-----|
| Month 1 | [X] | [X] | [X] | [X] | $[X] |
[continue for 6 months]

**3. Unit Economics**:
- CAC (Customer Acquisition Cost): How much to get a user?
- LTV (Lifetime Value): How much is a user worth?
- LTV/CAC ratio (target: >3x)
- Payback period

**4. Revenue Sources** (ranked by timeline):
1. GitHub Sponsors (now — small but signals community support)
2. Pro subscriptions (3-6 months)
3. Team licenses (6-12 months)
4. Enterprise contracts (12-18 months)
5. Partnerships/affiliates (ongoing)

**5. CEO Briefing**:
- Where we are (brutally honest)
- Where we need to be
- What's working
- What's blocked
- Top 3 revenue actions for next month

Provide the complete revenue report with specific numbers and forecasts."""
        )

        await self.memory.remember("revenue_report", result[:600], category="revenue")
        await self.send_message("ceo", f"Revenue Report: {result[:400]}", "business")
        return result

    # ── Strategic Alliances ────────────────────────────────
    async def _strategic_alliance(self, description: str) -> str:
        """Build long-term strategic alliances with complementary companies."""
        result = await self.think(
            f"""Strategic alliance task: {description}

Product: {settings.product_name}

**1. Alliance Targets** (complementary, not competitive):

**Open Source Security Tools** (mutual ecosystem):
- Nmap — recon integration
- OWASP ZAP — web scanning integration
- Metasploit — exploitation integration
- Nuclei/ProjectDiscovery — vulnerability scanning
- Benefit: Combined workflow, shared users

**AI/LLM Ecosystem**:
- Ollama — local model provider
- LangChain/LlamaIndex — framework integration
- OpenAI/Anthropic — featured project
- Benefit: Technology partnerships, showcase

**Cloud/DevOps**:
- DigitalOcean — startups program / credits
- GitHub — featured project / Arctic Code Vault
- Docker — official image listing
- Benefit: Infrastructure, visibility

**2. Alliance Value Matrix**:
| Partner | We Get | They Get | Effort | Priority |
|---------|--------|----------|--------|----------|
| Nmap | Integration credibility | AI-augmented scanning | Medium | High |
| Ollama | Local model support | AI security use case | Low | High |
| DigitalOcean | Credits + listing | Startup success story | Low | Medium |

**3. Alliance Proposal Template**:
- Intro: Who we are, what we've built
- Alignment: Why our missions complement each other
- Proposal: Specific collaboration model
- Mutual benefit: What each side gains
- Next step: Low-commitment first step

Write 2 complete alliance proposals for highest-priority targets."""
        )

        await self.memory.remember("alliances", result[:400], category="alliances")
        await self.send_message("ceo", f"Alliance Proposals: {result[:300]}", "business")
        return result

    # ── Market Expansion ───────────────────────────────────
    async def _market_expansion(self, description: str) -> str:
        """Identify new markets, verticals, and use cases."""
        result = await self.think(
            f"""Market expansion task: {description}

Product: {settings.product_name} — AI pentesting chatbot
Current Market: Individual security researchers and ethical hackers

**1. Adjacent Markets**:

**DevSecOps** (shift-left security):
- Use case: Developers scanning their own code
- Entry point: GitHub integration, CI/CD security checks
- Size: Large and growing fast

**Security Education**:
- Use case: Teaching pentesting with AI assistance
- Entry point: University partnerships, CTF integration
- Size: Medium, high retention

**Compliance & Audit**:
- Use case: Automated security compliance checks
- Entry point: Report generation, checklist automation
- Size: Large, high willingness to pay

**Incident Response**:
- Use case: AI-assisted threat analysis
- Entry point: Integration with SIEM/SOAR tools
- Size: Large, enterprise-heavy

**2. Geographic Expansion**:
- Current: English-speaking markets
- Next: EU (GDPR angle), Asia (CTF community strong)
- Localization: Multilingual prompts and docs

**3. Vertical Expansion**:
| Vertical | Entry Strategy | Revenue Potential |
|----------|---------------|------------------|
| MSSPs | White-label solution | High |
| Government | Compliance-focused | Very High |
| Finance | Regulatory requirements | Very High |
| Healthcare | HIPAA security | High |
| Education | Free tier + research | Low (but strategic) |

**4. New Use Cases** (beyond pentesting):
- Vulnerability assessment
- Security training simulator
- Threat intelligence analysis
- Security report writing
- Compliance checking

**5. Market Entry Framework**:
For each new market:
- Market size and growth
- Key buyers and decision makers
- Required product changes
- Go-to-market strategy
- Timeline and investment

Analyze the top 2 expansion opportunities with full go-to-market plans."""
        )

        await self.memory.remember("market_expansion", result[:600], category="expansion")
        await self.send_message("ceo", f"Market Expansion: {result[:400]}", "business")
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
        """Sales generates a revenue & partnerships executive report."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]

        pipeline = await self.memory.recall("sales_pipeline", "pipeline")
        revenue = await self.memory.recall("revenue_report", "revenue")
        competitive = await self.memory.recall("competitive_intel", "competitive")

        report = await self.think(
            f"""Generate the Sales & BD daily report.

## Sales Tasks Today
{json.dumps(today_tasks, indent=2) if today_tasks else 'No sales tasks today.'}

## Pipeline Status
{pipeline[:300] if pipeline else 'No pipeline data yet.'}

## Revenue Status
{revenue[:200] if revenue else 'Pre-revenue.'}

## Competitive Landscape
{competitive[:200] if competitive else 'Not analysed yet.'}

Write a concise sales report:
1. Sales activities completed today
2. Pipeline health: [X] leads, [X] active, [X] warm
3. Key deals/opportunities in progress
4. Outreach sent and response rate
5. Partnership/alliance progress
6. Revenue status / forecast
7. Top 3 priorities for tomorrow
8. CEO attention needed (if any)

Under 250 words. Be specific and deal-focused."""
        )

        await state_manager.save_daily_report(self.agent_id, report)
        return f"**Sales & Business Development Report**\n{report}"
