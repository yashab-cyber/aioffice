# 🏢 AI Office v2.0 — Autonomous Startup Growth System

An AI-powered virtual office where **9 autonomous agents** work together to grow your startup. Each agent has a specialized role with 10–16 task types, persistent memory with importance scoring, inter-agent communication with priority & delegation, performance tracking, and crash-resilient state recovery.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.112-green)
![LLM](https://img.shields.io/badge/LLM-10%20Providers-purple)
![Agents](https://img.shields.io/badge/Agents-9-orange)

## 🎯 What It Does

- **9 AI Agents** work autonomously in a pixel-art virtual office
- **CEO** (10 task types) — strategy, OKRs, performance reviews, competitive analysis, coaching
- **CTO** (14 task types) — architecture, roadmaps, code quality, security reviews, release management
- **CMO** (13 task types) — brand strategy, campaigns, content calendars, SEO, analytics
- **CXO** (14 task types) — user journeys, onboarding, UX audits, NPS, retention strategy
- **Marketing** (16 task types) — social media, blogs, SEO, Product Hunt, growth hacking, ads
- **Sales** (16 task types) — outreach, cold email, partnerships, enterprise, pipeline management
- **HR** (15 task types) — monitoring, culture, burnout checks, org charts, workload balance
- **IT** (16 task types) — CI/CD, Docker, security, monitoring, infrastructure, compliance
- **Discord** (16 task types) — server setup, events, bots, moderation, ambassador programs
- **10 LLM providers** — OpenAI, Anthropic, Gemini, Ollama, Groq, OpenRouter, Mistral, Together AI, DeepSeek, Custom/Local
- **Persistent memory** with importance scoring and auto-cleanup
- **Agent delegation** — agents can delegate tasks to each other
- **Performance metrics** — task completion tracking, duration, analytics
- **State saving** — crash-resistant, resumes where it left off
- **Daily Telegram reports** — evening summary sent to the director
- **Director commands** — message or delegate tasks to any agent from the GUI
- **Health monitoring** — comprehensive health checks for all agents and database
- **Pixel art GUI** — retro-style office with neon glows, particles, and live status

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd aioffice
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and set your keys:

| Variable | Required | Description |
|---|---|---|
| `LLM_PROVIDER` | ✅ | Provider to use: `openai`, `anthropic`, `gemini`, `ollama`, `groq`, `openrouter`, `mistral`, `together`, `deepseek`, `custom` |
| `OPENAI_API_KEY` | Per provider | OpenAI API key (GPT-4o) |
| `ANTHROPIC_API_KEY` | Per provider | Anthropic API key (Claude) |
| `GEMINI_API_KEY` | Per provider | Google Gemini API key |
| `OLLAMA_BASE_URL` | Per provider | Ollama local URL (default: localhost:11434) |
| `TELEGRAM_BOT_TOKEN` | Optional | For daily report delivery |
| `TELEGRAM_CHAT_ID` | Optional | Your Telegram chat ID |
| `SMTP_HOST/USER/PASSWORD` | Optional | For email outreach |

See [.env.example](.env.example) for all 50+ configuration variables including LLM tuning, agent tuning, feature flags, and webhooks.

### 3. Run

```bash
python main.py
```

Open **http://localhost:8000** in your browser.

### Docker

```bash
docker-compose up -d
```

## 🖥️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI Server v2.0                           │
│                                                                   │
│   ┌─── Leadership Team ───────────────────────────────────────┐  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────────┐  │  │
│   │  │   CEO   │  │   CTO   │  │   CMO   │  │    CXO     │  │  │
│   │  │ 10 tasks│  │ 14 tasks│  │ 13 tasks│  │  14 tasks  │  │  │
│   │  └────┬────┘  └────┬────┘  └────┬────┘  └─────┬──────┘  │  │
│   └───────┼─────────────┼───────────┼──────────────┼─────────┘  │
│           │             │           │              │             │
│   ┌───────┴─────────────┴───────────┴──────────────┴─────────┐  │
│   │         Message Bus (Priority + Channels + Delegation)    │  │
│   └───────┬─────────────┬───────────┬─────────────┬──────────┘  │
│           │             │           │             │              │
│   ┌─── Growth ──────┐ ┌┴─ Ops ────┐│  ┌── Community ──┐       │
│   │┌────────┐┌──────┐│ │┌────┐┌───┐││  │ ┌──────────┐ │       │
│   ││Marketng││Sales ││ ││ HR ││ IT│││  │ │ Discord  │ │       │
│   ││16 tasks││16 tsk││ ││15tk││16t│││  │ │ 16 tasks │ │       │
│   │└────────┘└──────┘│ │└────┘└───┘││  │ └──────────┘ │       │
│   └──────────────────┘ └──────────┘│  └──────────────┘        │
│                                                                   │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  Memory (Importance Scoring) │ Metrics │ State Recovery  │   │
│   │  LLM (10 Providers + Retry)  │ Health  │ Telegram Bot    │   │
│   └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
aioffice/
├── main.py                  # Entry point (configurable logging)
├── server.py                # FastAPI server + 30+ API routes
├── config.py                # 50+ settings (from .env)
├── agents/
│   ├── base_agent.py        # Base class — AI, memory, delegation, metrics, health
│   ├── registry.py          # Agent registry with teams & health checks
│   ├── ceo.py               # CEO — 10 task types, strategy & coordination
│   ├── cto.py               # CTO — 14 task types, tech & architecture
│   ├── cmo.py               # CMO — 13 task types, marketing strategy
│   ├── cxo.py               # CXO — 14 task types, user experience
│   ├── marketing_team.py    # Marketing — 16 task types, content & growth
│   ├── sales_team.py        # Sales — 16 task types, outreach & BD
│   ├── hr.py                # HR — 15 task types, monitoring & culture
│   ├── it_team.py           # IT — 16 task types, infrastructure & security
│   └── discord_team.py      # Discord — 16 task types, community management
├── core/
│   ├── database.py          # SQLite — 7 tables, migrations, stats
│   ├── memory.py            # Memory with importance scoring & auto-cleanup
│   ├── communication.py     # Message bus — priority, channels, analytics
│   ├── state_manager.py     # State, metrics, task analytics, delegations
│   ├── office_manager.py    # Orchestrator with health monitoring
│   └── llm_provider.py      # 10 LLM providers with factory pattern
├── tools/
│   ├── web_browser.py       # Web search & scraping
│   ├── email_sender.py      # SMTP email
│   └── telegram_bot.py      # Telegram reports
├── gui/
│   ├── templates/index.html # Pixel art office UI
│   └── static/
│       ├── css/office.css   # Neon glow pixel art styles
│       └── js/app.js        # Live updates & interaction
├── Dockerfile               # Multi-stage build, non-root, health check
├── docker-compose.yml        # With health checks & resource limits
└── .env.example             # 50+ configuration variables
```

## ⚙️ Configuration

### LLM Tuning
| Variable | Default | Description |
|---|---|---|
| `MAX_TOKENS_PER_CALL` | 4000 | Max tokens per LLM response |
| `LLM_MAX_RETRIES` | 3 | Retry attempts with exponential backoff |
| `LLM_RATE_LIMIT_DELAY` | 0.5 | Min seconds between LLM calls |
| `MEMORY_CONTEXT_ITEMS` | 30 | Memory items injected into prompts |

### Agent Tuning
| Variable | Default | Description |
|---|---|---|
| `TASKS_PER_CYCLE` | 8 | Max tasks each agent runs per cycle |
| `TASK_TIMEOUT` | 300 | Seconds before a task is killed |
| `TASK_DELAY` | 2.0 | Seconds between tasks |
| `CYCLE_DELAY` | 45.0 | Seconds between work cycles |
| `AGENT_CYCLE_TIMEOUT` | 600 | Max seconds for an agent's full cycle |

### Feature Flags
| Variable | Default | Description |
|---|---|---|
| `ENABLE_DELEGATION` | true | Allow inter-agent task delegation |
| `ENABLE_CROSS_AGENT_CONTEXT` | true | Agents see each other's activity |
| `ENABLE_MEMORY_CLEANUP` | true | Auto-remove old low-importance memories |
| `MEMORY_MAX_ENTRIES` | 1000 | Max memory entries per agent |

## 🎮 GUI Features

- **Pixel art office** with desks, monitors, chairs, plants, and a water cooler
- **Neon glow effects** and ambient particles
- **Click any agent** to see their tasks, memory, and status
- **Live status updates** via Server-Sent Events (SSE)
- **Director console** — send messages or delegate tasks to any agent
- **Generate reports** on demand
- **Speech bubbles** show what each agent is currently working on

## 🔄 State & Recovery

The office **auto-saves state** every cycle:
- Agent status, tasks completed/failed, LLM call counts, cycle counts
- All task logs with duration tracking
- Agent memories with importance scoring and access counts
- Inter-agent messages with priority levels
- Performance metrics time series
- Delegation tracking

If the process crashes, the next startup **resumes from the last saved state**.

## 📱 Telegram Reports

At the configured `REPORT_HOUR` (default: 18:00 UTC), all agents generate their daily report and it's sent to your Telegram chat. You can also trigger it manually from the GUI.

## 🔧 API Endpoints

### Office
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Office GUI |
| `GET` | `/api/status` | Office status |
| `GET` | `/api/health` | Comprehensive health check |
| `GET` | `/api/health/agents` | All agents health |
| `GET` | `/api/health/db` | Database statistics |
| `GET` | `/api/config` | Non-sensitive configuration |
| `POST` | `/api/office/stop` | Stop office |
| `POST` | `/api/office/restart` | Restart office |

### Agents
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/agents` | All agents |
| `GET` | `/api/agents/{id}` | Agent detail |
| `GET` | `/api/agents/{id}/health` | Agent health check |
| `GET` | `/api/agents/{id}/memory` | Agent memories |
| `GET` | `/api/agents/{id}/memory/stats` | Memory statistics |
| `GET` | `/api/agents/{id}/memory/search?q=` | Search agent memory |
| `GET` | `/api/agents/{id}/tasks` | Agent task log (filterable) |
| `GET` | `/api/agents/{id}/metrics` | Agent performance metrics |

### Teams & Registry
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/registry` | Full registry with metadata |
| `GET` | `/api/teams` | Team structure |
| `GET` | `/api/teams/{team}` | Team members & status |

### Communication
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/messages` | All messages |
| `GET` | `/api/messages/{id}` | Agent messages |
| `GET` | `/api/messages/search/{q}` | Search messages |
| `GET` | `/api/messages/stats` | Message analytics |
| `GET` | `/api/events` | SSE stream |

### Tasks & Reports
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/tasks` | All tasks |
| `GET` | `/api/tasks/analytics` | Task analytics dashboard |
| `GET` | `/api/reports` | Daily reports |
| `GET` | `/api/reports/dates` | Available report dates |
| `POST` | `/api/reports/generate` | Force generate report |

### Director Commands
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/director/message` | Send message to agent(s) |
| `POST` | `/api/director/delegate` | Delegate task to agent |

### LLM
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/llm/providers` | Supported LLM providers |
| `GET` | `/api/llm/status` | Active LLM status |

## 📋 Product Focus

Currently configured to grow **[HackBot](https://github.com/yashab-cyber/hackbot)** — an AI-powered penetration testing chatbot.

Discord: https://discord.gg/X2tgYHXYq

## License

MIT