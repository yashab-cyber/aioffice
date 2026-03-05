# 🏢 AI Office — Autonomous Startup Growth System

An AI-powered virtual office where autonomous agents work together to grow your startup. Each agent has a specific role (CEO, CTO, CMO, CXO, Marketing, Sales, HR), persistent memory, inter-agent communication, and the ability to resume from saved state after any interruption.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.112-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-purple)

## 🎯 What It Does

- **7 AI Agents** work autonomously in a pixel-art virtual office
- **CEO** sets strategy and coordinates the team
- **CTO** manages GitHub, technical content, and developer experience
- **CMO** designs marketing strategy and campaigns
- **CXO** handles user experience and community
- **Marketing Team** creates content, social media posts, community outreach
- **Sales Team** identifies partners, writes outreach emails
- **HR** monitors all agents and tracks productivity
- **Persistent memory** — agents remember past decisions and context
- **State saving** — crash-resistant, resumes where it left off
- **Daily Telegram reports** — evening summary sent to the director
- **Director commands** — you can message any agent from the GUI
- **Pixel art GUI** — retro-style office with live agent status

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
| `OPENAI_API_KEY` | ✅ | OpenAI API key (GPT-4o recommended) |
| `TELEGRAM_BOT_TOKEN` | Optional | For daily report delivery |
| `TELEGRAM_CHAT_ID` | Optional | Your Telegram chat ID |
| `SMTP_HOST/USER/PASSWORD` | Optional | For email outreach |

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
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Server                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────────┐ │
│  │   CEO   │  │   CTO   │  │   CMO   │  │    CXO     │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────┬──────┘ │
│       │            │            │              │         │
│  ┌────┴────────────┴────────────┴──────────────┴─────┐  │
│  │              Message Bus (SQLite)                  │  │
│  └────┬────────────┬────────────┬──────────────┬─────┘  │
│       │            │            │              │         │
│  ┌────┴────┐  ┌────┴────┐  ┌───┴─────┐  ┌────┴─────┐  │
│  │Marketing│  │  Sales  │  │   HR    │  │  State   │  │
│  │  Team   │  │  Team   │  │ Monitor │  │ Manager  │  │
│  └─────────┘  └─────────┘  └─────────┘  └──────────┘  │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Persistent Memory │ State Recovery │ Telegram Bot  │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
aioffice/
├── main.py                  # Entry point
├── server.py                # FastAPI server + API routes
├── config.py                # Settings (from .env)
├── agents/
│   ├── base_agent.py        # Base class with AI, memory, state
│   ├── registry.py          # Agent registration
│   ├── ceo.py               # CEO — strategy & coordination
│   ├── cto.py               # CTO — tech & GitHub
│   ├── cmo.py               # CMO — marketing strategy
│   ├── cxo.py               # CXO — user experience
│   ├── marketing_team.py    # Marketing — content creation
│   ├── sales_team.py        # Sales — outreach & BD
│   └── hr.py                # HR — monitoring & reports
├── core/
│   ├── database.py          # SQLite setup & schema
│   ├── memory.py            # Agent memory system
│   ├── communication.py     # Inter-agent message bus
│   ├── state_manager.py     # State persistence & recovery
│   └── office_manager.py    # Office orchestrator
├── tools/
│   ├── web_browser.py       # Web search & scraping
│   ├── email_sender.py      # SMTP email
│   └── telegram_bot.py      # Telegram reports
├── gui/
│   ├── templates/index.html # Pixel art office UI
│   └── static/
│       ├── css/office.css   # Pixel art styles
│       └── js/app.js        # Live updates & interaction
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## 🎮 GUI Features

- **Pixel art office** with desks, monitors, chairs, plants, and a water cooler
- **Click any agent** to see their tasks, memory, and status
- **Live status updates** via Server-Sent Events (SSE)
- **Director console** — send messages to any agent or broadcast to all
- **Generate reports** on demand
- **Speech bubbles** show what each agent is currently working on

## 🔄 State Persistence

The office **auto-saves state** every cycle:
- Agent positions, status, current task
- All task logs and results
- Agent memories (decisions, insights, completed work)
- Inter-agent messages

If the process crashes or you shut down, the next startup **resumes from the last saved state** — agents pick up where they left off.

## 📱 Telegram Reports

At the configured `REPORT_HOUR` (default: 18:00 UTC), all agents generate their daily report and it's sent to your Telegram chat. You can also trigger it manually from the GUI.

## 🔧 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Office GUI |
| `GET` | `/api/status` | Office status |
| `GET` | `/api/agents` | All agents |
| `GET` | `/api/agents/{id}` | Agent detail |
| `GET` | `/api/agents/{id}/memory` | Agent memories |
| `GET` | `/api/agents/{id}/tasks` | Agent task log |
| `GET` | `/api/messages` | All messages |
| `GET` | `/api/events` | SSE stream |
| `GET` | `/api/reports` | Daily reports |
| `POST` | `/api/director/message` | Send director message |
| `POST` | `/api/reports/generate` | Force report |
| `POST` | `/api/office/stop` | Stop office |
| `POST` | `/api/office/restart` | Restart office |

## 📋 Product Focus

Currently configured to grow **[HackBot](https://github.com/yashab-cyber/hackbot)** — an AI-powered penetration testing chatbot.

Discord: https://discord.gg/X2tgYHXYq

## License

MIT