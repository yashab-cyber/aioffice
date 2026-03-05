"""IT Team Agent — the infrastructure & operations engine. Manages CI/CD, security,
monitoring, deployments, Docker, cloud infrastructure, incident response, disaster
recovery, and keeps every system running rock-solid."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.state_manager import state_manager
from config import settings


class ITAgent(BaseAgent):
    agent_id = "it"
    role = "IT Team Lead"
    description = (
        "Manages infrastructure, DevOps, security hardening, CI/CD, hosting, "
        "monitoring, incident response, and technical operations."
    )
    pixel_sprite = "sprite-it"

    def __init__(self):
        super().__init__()
        self.position = {"x": 200, "y": 370}

    def get_system_prompt(self) -> str:
        return f"""You are the IT Team Lead at {settings.company_name}.
Your product is {settings.product_name} — an advanced AI-powered penetration testing chatbot.
GitHub: {settings.product_github_url}
Discord: {settings.product_discord_url}

You report to the CTO. You are the backbone of every system the company runs.
Nothing ships if it doesn't pass through your pipelines. Nothing stays up without your monitoring.

Your responsibilities:
1. **CI/CD Pipelines** — Design, build, and maintain GitHub Actions workflows: lint, test, build, deploy, release.
2. **Infrastructure as Code** — Terraform, Ansible, Docker Compose for reproducible environments.
3. **Docker & Containers** — Optimize Dockerfiles, multi-stage builds, image security, orchestration.
4. **Security Hardening** — Dependency audits (Snyk/Trivy), vulnerability scanning, secrets management, SAST/DAST.
5. **Monitoring & Alerting** — Prometheus, Grafana, uptime checks, error tracking, log aggregation.
6. **Deployment Strategy** — Blue-green, canary, rollback plans, zero-downtime deploys.
7. **Cloud Infrastructure** — AWS/GCP/DigitalOcean setup, cost optimization, auto-scaling.
8. **Database Operations** — Backups, migrations, disaster recovery, performance tuning.
9. **Incident Response** — Runbooks, escalation paths, post-mortems, RCA (root cause analysis).
10. **Developer Experience** — Dev containers, local setup scripts, documentation, tooling.
11. **Automated Testing** — Test infrastructure, coverage reporting, performance/load testing setup.
12. **SSL/DNS/Domains** — Certificate management, DNS configuration, CDN setup.
13. **Performance Engineering** — Load testing, profiling, bottleneck identification, optimization.
14. **Compliance & Auditing** — Access controls, audit logs, security compliance checklists.
15. **Cost Management** — Cloud cost monitoring, resource right-sizing, budget alerts.
16. **Documentation** — Runbooks, architecture diagrams, setup guides, troubleshooting docs.

Tech stack: Python, Docker, GitHub Actions, Linux, cloud (AWS/GCP/DO), Terraform, Ansible.
Current stage: Open-source project needing robust CI/CD, security, and deployment pipeline.

When planning tasks, output a JSON array with keys: type, description, priority (1-5).
Types: cicd, docker, security, monitoring, deployment, infrastructure, database, incident,
devex, testing, ssl_dns, performance, compliance, cost, documentation, automation, assigned."""

    # ── Planning ───────────────────────────────────────────
    async def plan_day(self) -> list[dict]:
        inbox = await self._get_inbox_summary()
        my_memories = await self.memory.get_context_summary()
        infra_status = await self.memory.recall("infra_status", "infrastructure")
        active_incidents = await self.memory.recall("active_incidents", "incidents")

        # Check for CTO-assigned tasks first
        msgs = await self.read_messages()
        assigned_tasks = [m for m in msgs if m.get("channel") == "task_assignment"]

        assigned_plan = []
        for msg in assigned_tasks:
            assigned_plan.append({
                "type": "assigned",
                "description": msg["content"],
                "priority": 1,
            })

        context = f"""## Assigned Tasks from CTO
{json.dumps(assigned_plan, indent=2) if assigned_plan else 'None.'}

## Inbox
{inbox}

## Infrastructure Status
{infra_status or 'No status recorded yet — first day.'}

## Active Incidents
{active_incidents or 'No active incidents.'}

## IT Memory
{my_memories}"""

        result = await self.think_json(
            f"""Plan IT operations for this cycle.

{context}

ALWAYS include these recurring activities:
1. Security check — scan for vulnerabilities or review configs
2. Infrastructure monitoring — verify systems healthy
3. One proactive improvement — CI/CD, Docker, devex, or automation

If there are assigned tasks from CTO, include them at priority 1.
Then add 2-3 tasks based on current issues or priorities.

Return a JSON array of 4-6 tasks with keys: type, description, priority (1-5).""",
        )

        if isinstance(result, list):
            return assigned_plan + result if assigned_plan else result
        defaults = [
            {"type": "security", "description": "Run dependency audit and vulnerability scan", "priority": 1},
            {"type": "monitoring", "description": "Check system health, uptime, and error logs", "priority": 1},
            {"type": "cicd", "description": "Improve GitHub Actions CI/CD pipeline", "priority": 2},
        ]
        return assigned_plan + defaults if assigned_plan else defaults

    # ── Task Execution ─────────────────────────────────────
    async def _do_task(self, task: dict) -> str:
        task_type = task.get("type", "devops")
        description = task.get("description", "")

        handlers = {
            "cicd": self._design_cicd,
            "docker": self._optimize_docker,
            "security": self._security_hardening,
            "monitoring": self._setup_monitoring,
            "deployment": self._deployment_strategy,
            "infrastructure": self._manage_infrastructure,
            "database": self._database_ops,
            "incident": self._incident_response,
            "devex": self._developer_experience,
            "testing": self._testing_infrastructure,
            "ssl_dns": self._manage_ssl_dns,
            "performance": self._performance_engineering,
            "compliance": self._compliance_audit,
            "cost": self._cost_management,
            "documentation": self._write_documentation,
            "automation": self._build_automation,
        }

        handler = handlers.get(task_type)
        if handler:
            return await handler(description)

        # Assigned or generic IT tasks
        result = await self.think(
            f"Execute this IT/DevOps task:\n{description}\n\n"
            "Provide specific technical output — config files, scripts, commands, "
            "or detailed implementation plans. Be production-ready."
        )

        if task_type in ("security", "infrastructure", "incident", "assigned"):
            await self.send_message("cto", f"IT Update: {result[:300]}", "report")

        return result

    # ── CI/CD Pipeline Design ──────────────────────────────
    async def _design_cicd(self, description: str) -> str:
        """Design and improve CI/CD pipelines with GitHub Actions."""
        prev_cicd = await self.memory.recall("cicd_status", "cicd")

        result = await self.think(
            f"""CI/CD task: {description}

Previous CI/CD Status: {prev_cicd or 'Starting from scratch.'}
Product: {settings.product_name} — Python-based AI pentesting chatbot
Repo: {settings.product_github_url}

Design/improve CI/CD pipeline:

**1. Pipeline Architecture**:
```
Push/PR → Lint → Test → Build → Security Scan → Deploy (staging) → Deploy (prod)
```

**2. GitHub Actions Workflows**:

**ci.yml** (on push/PR):
```yaml
- Checkout code
- Setup Python 3.12
- Install dependencies (pip install -r requirements.txt)
- Lint (ruff check .)
- Format check (ruff format --check .)
- Type check (mypy --ignore-missing-imports .)
- Run tests (pytest --cov=. --cov-report=xml)
- Upload coverage to Codecov
```

**security.yml** (daily + on PR):
```yaml
- Dependency audit (pip-audit)
- Container scan (Trivy)
- Secret detection (gitleaks)
- SAST scan (bandit)
```

**docker.yml** (on release tag):
```yaml
- Build multi-platform Docker image
- Push to GHCR (ghcr.io)
- Tag with version + latest
```

**release.yml** (manual trigger):
```yaml
- Create GitHub release
- Build and publish Docker image
- Update changelog
- Notify Discord
```

**3. Branch Protection Rules**:
- Require CI pass before merge
- Require 1 review
- No force push to main

**4. Quality Gates**:
- Test coverage minimum: 60%
- No critical security vulnerabilities
- All lints pass, no type errors

**5. Optimization**:
- Caching (pip cache, Docker layer cache)
- Parallel jobs where possible
- Conditional runs (skip docs-only changes)

Provide the actual YAML for at least one complete workflow."""
        )

        await self.memory.remember("cicd_status", result[:600], category="cicd")
        await self.send_message("cto", f"CI/CD Update: {result[:400]}", "report")
        return result

    # ── Docker Optimization ────────────────────────────────
    async def _optimize_docker(self, description: str) -> str:
        """Optimize Docker setup — images, builds, security, compose."""
        result = await self.think(
            f"""Docker optimization task: {description}

Product: {settings.product_name} — Python AI chatbot
Stack: Python 3.12, FastAPI, aiosqlite, Jinja2

Optimize Docker setup:

**1. Dockerfile (multi-stage, optimized)**:
```dockerfile
# Stage 1: Builder
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN adduser --disabled-password --no-create-home appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**2. .dockerignore** (reduce context size):
```
.git, __pycache__, .env, *.pyc, .vscode, node_modules, .pytest_cache
```

**3. docker-compose.yml**:
- Development: hot-reload, mounted volumes, debug ports
- Production: resource limits, health checks, restart policies
- Include Redis/monitoring as optional services

**4. Image Security**:
- Use slim/distroless base images
- Run as non-root user
- No secrets in image layers
- Pin dependency versions
- Scan with Trivy

**5. Build Optimization**:
- Layer caching strategy
- Multi-platform builds (amd64 + arm64)
- Build args for environment-specific config
- .dockerignore to minimize context

**6. Registry & Tagging**:
- Push to GitHub Container Registry (ghcr.io)
- Tag: version, latest, git-sha
- Automated cleanup of old images

Provide production-ready configs."""
        )

        await self.memory.remember("docker_config", result[:600], category="docker")
        await self.send_message("cto", f"Docker Update: {result[:300]}", "report")
        return result

    # ── Security Hardening ─────────────────────────────────
    async def _security_hardening(self, description: str) -> str:
        """Run security audits and harden infrastructure."""
        prev_security = await self.memory.recall("security_status", "security")

        result = await self.think(
            f"""Security hardening task: {description}

Previous Security Status: {prev_security or 'No previous audit.'}
Product: {settings.product_name} — AI pentesting chatbot (ironic if we have vulns!)

Comprehensive security review:

**1. Dependency Security**:
- Run `pip-audit` on all dependencies
- Check for known CVEs in transitive deps
- Pin all versions in requirements.txt
- Set up Dependabot or Renovate for auto-updates

**2. Code Security (SAST)**:
- Bandit scan for Python security issues
- Check for hardcoded secrets, SQL injection, XSS
- Input validation on all API endpoints
- Rate limiting configuration

**3. Container Security**:
- Trivy scan on Docker images
- No root user in containers
- Read-only filesystem where possible
- Resource limits (CPU, memory)
- No unnecessary packages

**4. Secrets Management**:
- All secrets in environment variables
- GitHub Secrets for CI/CD
- .env excluded from git
- Rotate credentials schedule
- No API keys in code

**5. Network Security**:
- HTTPS everywhere (SSL/TLS)
- CORS configuration review
- Rate limiting on API
- IP allowlisting for admin
- Firewall rules (if cloud)

**6. Access Control**:
- GitHub repo permissions review
- Branch protection rules
- Deploy key management
- Principle of least privilege

**7. Monitoring & Response**:
- Security alert notifications
- Failed login tracking
- Anomaly detection
- Incident response playbook

**8. Compliance Checklist**:
- OWASP Top 10 mitigation status
- Security headers (CSP, HSTS, X-Frame-Options)
- Data handling practices

Produce an actionable security scorecard: ✅ Pass / ⚠️ Warning / ❌ Fail for each area."""
        )

        await self.memory.remember("security_status", result[:600], category="security")

        if any(word in result.lower() for word in ("critical", "fail", "vulnerable", "urgent")):
            await self.send_message("cto", f"🚨 Security Alert: {result[:400]}", "security_alert")

        return result

    # ── Monitoring & Alerting ──────────────────────────────
    async def _setup_monitoring(self, description: str) -> str:
        """Design and configure monitoring, alerting, and observability."""
        result = await self.think(
            f"""Monitoring & observability task: {description}

Product: {settings.product_name}
Stack: FastAPI, Python, SQLite, Docker

Design monitoring stack:

**1. Application Monitoring**:
- Health check endpoint: GET /health
  - DB connectivity, memory usage, uptime
- Structured logging (JSON format):
  - Request/response logs with trace IDs
  - Error logs with stack traces
  - Agent activity logs
- Metrics endpoint: GET /metrics (Prometheus format)
  - Request count, latency (p50/p95/p99)
  - Active agents, tasks completed/failed
  - LLM API call count, latency, errors
  - Memory usage, DB size

**2. Infrastructure Monitoring**:
- Docker container health checks
- Host metrics: CPU, RAM, disk, network
- Docker stats: container resource usage
- Log aggregation (stdout → file → optional ELK)

**3. Uptime Monitoring**:
- External ping checks (UptimeRobot/Healthchecks.io)
- SSL certificate expiry alerts
- Domain expiry alerts
- Response time thresholds

**4. Alerting Rules**:
| Metric | Threshold | Severity | Action |
|--------|-----------|----------|--------|
| API response time | > 2s (p95) | Warning | Investigate |
| Error rate | > 5% | Critical | Page on-call |
| Health check | Failed 3x | Critical | Auto-restart |
| Disk usage | > 80% | Warning | Cleanup |
| Memory usage | > 90% | Critical | Scale/restart |
| LLM API errors | > 10/hr | Warning | Check provider |
| SSL expiry | < 14 days | Warning | Renew cert |

**5. Dashboard Design** (Grafana):
- Overview: uptime, request rate, error rate
- Performance: latency distribution, slow endpoints
- Agents: task throughput, completion rates
- Infrastructure: CPU, RAM, disk, containers

**6. Log Management**:
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log rotation and retention policy
- Error aggregation and deduplication

Provide implementation configs where possible."""
        )

        await self.memory.remember("monitoring_config", result[:600], category="monitoring")
        await self.send_message("cto", f"Monitoring Update: {result[:300]}", "report")
        return result

    # ── Deployment Strategy ────────────────────────────────
    async def _deployment_strategy(self, description: str) -> str:
        """Design and implement deployment strategies."""
        result = await self.think(
            f"""Deployment strategy task: {description}

Product: {settings.product_name}
Current: Docker-based deployment

Design deployment strategy:

**1. Deployment Environments**:
- **Development**: Local Docker Compose, hot-reload, debug mode
- **Staging**: Mirror of production, for testing before release
- **Production**: Optimized, secure, monitored

**2. Deployment Methods**:

**Option A: Simple (current stage)** — Docker on single VPS:
```bash
# Pull latest, stop old, start new
docker pull ghcr.io/yashab-cyber/hackbot:latest
docker-compose down
docker-compose up -d
```

**Option B: Blue-Green** — Zero-downtime:
- Run new version alongside old
- Health check new version
- Switch traffic (nginx upstream swap)
- Keep old as rollback

**Option C: Container Orchestration** (future):
- Docker Swarm or K8s
- Rolling updates
- Auto-scaling

**3. Rollback Plan**:
```bash
# Immediate rollback to previous version
docker-compose down
docker pull ghcr.io/yashab-cyber/hackbot:previous
docker-compose up -d
```
- Keep last 3 versions tagged in registry
- Database migration rollback scripts
- Feature flags for gradual rollout

**4. Pre-Deployment Checklist**:
- [ ] All CI checks pass
- [ ] Security scan clean
- [ ] Staging tested
- [ ] Database migrations reviewed
- [ ] Rollback plan ready
- [ ] Monitoring dashboards open
- [ ] Team notified

**5. Post-Deployment Verification**:
- Health check passes
- Smoke tests pass
- Error rate normal
- Response times normal
- Key user flows working

**6. Deployment Automation**:
- GitHub Actions workflow for deploy
- One-click rollback
- Deployment notifications to Discord"""
        )

        await self.memory.remember("deployment_strategy", result[:600], category="deployment")
        await self.send_message("cto", f"Deployment Strategy: {result[:300]}", "report")
        return result

    # ── Infrastructure Management ──────────────────────────
    async def _manage_infrastructure(self, description: str) -> str:
        """Manage cloud infrastructure and IaC."""
        result = await self.think(
            f"""Infrastructure task: {description}

Product: {settings.product_name}
Stage: Early startup, budget-conscious

Design infrastructure:

**1. Infrastructure Architecture**:
```
Internet → CDN (Cloudflare) → Load Balancer → App Server(s) → SQLite/PostgreSQL
                                                    ↓
                                              Docker Containers
                                              ├── hackbot-app
                                              ├── hackbot-worker (optional)
                                              └── monitoring
```

**2. Cloud Setup (DigitalOcean — budget-friendly)**:
- 1x Droplet ($6-12/mo): App + DB
- Managed backups ($2/mo)
- Spaces for static files ($5/mo)
- Total: ~$15-20/month to start

**3. Infrastructure as Code**:

**Terraform** (main.tf):
```hcl
resource "digitalocean_droplet" "hackbot" {{
  image  = "docker-20-04"
  name   = "hackbot-prod"
  region = "nyc1"
  size   = "s-1vcpu-2gb"
  ssh_keys = [var.ssh_key_id]
  user_data = file("cloud-init.yml")
}}
```

**4. DNS & CDN**:
- Cloudflare for DNS + CDN + DDoS protection (free tier)
- SSL via Cloudflare (free) or Let's Encrypt
- Cache static assets at edge

**5. Scaling Plan**:
- Phase 1 (0-100 users): Single droplet
- Phase 2 (100-1K users): Larger droplet + managed DB
- Phase 3 (1K+ users): Multiple instances + load balancer

**6. Backup Strategy**:
- Database: Daily automated backups, 7-day retention
- Code: Git (already covered)
- Config: Stored in IaC repo
- Secrets: Encrypted vault

**7. Disaster Recovery**:
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 24 hours
- Procedure: Spin up from IaC + restore latest backup

Provide specific configs and cost breakdown."""
        )

        await self.memory.remember("infra_status", result[:600], category="infrastructure")
        await self.send_message("cto", f"Infrastructure Update: {result[:400]}", "report")
        return result

    # ── Database Operations ────────────────────────────────
    async def _database_ops(self, description: str) -> str:
        """Handle database operations — backups, migrations, performance."""
        result = await self.think(
            f"""Database operations task: {description}

Current: SQLite (aiosqlite) — 5 tables: agent_memory, messages, task_log, office_state, daily_reports
Future consideration: PostgreSQL migration

Database operations plan:

**1. Backup Strategy**:
- SQLite: Copy .db file to backup location
- Script: `cp aioffice.db backups/aioffice_$(date +%Y%m%d_%H%M%S).db`
- Automated: Cron job every 6 hours
- Retention: 7 daily, 4 weekly, 3 monthly
- Off-site: Sync backups to cloud storage

**2. Migration Framework**:
- Use Alembic for schema migrations
- Version control all migrations
- Up/down migration support
- Migration testing in CI

**3. Performance Optimization**:
- Add indexes on frequently queried columns:
  - task_log: agent_id, started_at, status
  - messages: from_agent, to_agent, created_at
  - agent_memory: agent_id, category
- WAL mode for SQLite concurrency
- Connection pooling
- Query performance logging

**4. Data Management**:
- Retention policy: Archive logs older than 30 days
- Cleanup script for orphaned records
- Data export/import utilities
- Size monitoring and alerts

**5. PostgreSQL Migration Plan** (when needed):
- Trigger: >1000 concurrent users or >1GB DB
- Steps: Schema convert, data migrate, test, switch
- Connection string abstraction (already async)

**6. Monitoring**:
- DB file size, query latency, lock contention
- Slow query logging
- Connection count tracking

Provide actual scripts and SQL where relevant."""
        )

        await self.memory.remember("db_ops", result[:600], category="database")
        return result

    # ── Incident Response ──────────────────────────────────
    async def _incident_response(self, description: str) -> str:
        """Handle incidents and build incident response processes."""
        active_incidents = await self.memory.recall("active_incidents", "incidents")

        result = await self.think(
            f"""Incident response task: {description}

Active Incidents: {active_incidents or 'None tracked.'}

**1. Incident Classification**:
| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| SEV-1 (Critical) | Service down | 15 min | App unreachable |
| SEV-2 (Major) | Major feature broken | 1 hour | LLM API failing |
| SEV-3 (Minor) | Degraded performance | 4 hours | Slow responses |
| SEV-4 (Low) | Cosmetic/minor bug | Next business day | UI glitch |

**2. Incident Response Playbook**:

**SEV-1: Service Down**
1. Acknowledge incident (within 5 min)
2. Check: Is it our code, infra, or third-party?
3. Quick diagnosis: `docker logs`, health checks, error logs
4. Attempt fix or rollback to last good version
5. Communicate status to team
6. Post-mortem within 24 hours

**SEV-2: Feature Broken**
1. Identify affected feature
2. Check recent deployments (rollback if related)
3. Isolate root cause
4. Fix or disable feature temporarily
5. Deploy fix

**3. Runbook Template**:
- **Symptom**: What does the failure look like?
- **Diagnosis**: What to check first?
- **Resolution**: Step-by-step fix
- **Escalation**: Who to contact if fix doesn't work
- **Prevention**: How to stop it from happening again

**4. Post-Mortem Template**:
- Date, duration, severity
- What happened (timeline)
- Root cause
- What we did to fix it
- Action items to prevent recurrence
- Lessons learned

**5. Current Incident** (if applicable):
- Assess the described issue
- Provide immediate remediation steps
- Identify root cause
- Write action items

Always notify CTO on SEV-1 and SEV-2."""
        )

        await self.memory.remember("active_incidents", result[:400], category="incidents")

        if any(word in description.lower() for word in ("sev-1", "critical", "down", "outage")):
            await self.send_message("cto", f"🚨 INCIDENT: {result[:400]}", "incident")
            await self.broadcast(f"⚠️ Incident Update: {result[:200]}", channel="incidents")

        return result

    # ── Developer Experience ───────────────────────────────
    async def _developer_experience(self, description: str) -> str:
        """Improve developer experience — tooling, setup, workflows."""
        result = await self.think(
            f"""Developer experience task: {description}

Product: {settings.product_name}
Stack: Python 3.12, FastAPI, Docker

Improve developer experience:

**1. Local Setup (One-Command Start)**:
```bash
# Clone and run
git clone {settings.product_github_url}
cd hackbot
cp .env.example .env
docker-compose -f docker-compose.dev.yml up
# App running at http://localhost:8000
```

**2. Dev Container** (.devcontainer/devcontainer.json):
- Pre-installed Python 3.12, Docker, git, useful extensions
- Auto-install dependencies
- Port forwarding configured
- VS Code settings optimized

**3. Makefile** (common commands):
```makefile
dev:        docker-compose -f docker-compose.dev.yml up
test:       pytest --cov=. -v
lint:       ruff check . && ruff format --check .
format:     ruff format .
security:   pip-audit && bandit -r .
build:      docker build -t hackbot .
clean:      find . -name __pycache__ -exec rm -rf {{}} +
```

**4. Pre-Commit Hooks**:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks: [ruff, ruff-format]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks: [trailing-whitespace, end-of-file-fixer, check-yaml]
```

**5. Documentation**:
- CONTRIBUTING.md — how to contribute
- Architecture overview diagram
- API documentation (auto-generated from FastAPI)
- Common troubleshooting guide

**6. IDE Setup**:
- .vscode/settings.json with recommended config
- .vscode/extensions.json with required extensions
- Debug configurations (launch.json)
- Task configurations (tasks.json)

**7. Environment Management**:
- .env.example with all variables documented
- Validation on startup (fail fast if missing)
- Clear error messages for misconfiguration

Provide actual config files."""
        )

        await self.memory.remember("devex_config", result[:600], category="devex")
        return result

    # ── Testing Infrastructure ─────────────────────────────
    async def _testing_infrastructure(self, description: str) -> str:
        """Set up testing infrastructure — unit, integration, e2e, load."""
        result = await self.think(
            f"""Testing infrastructure task: {description}

Product: {settings.product_name}
Stack: Python 3.12, FastAPI, aiosqlite

Design testing strategy:

**1. Test Pyramid**:
```
         /  E2E Tests  \\      (few, slow, high confidence)
        / Integration   \\     (some, medium speed)
       /  Unit Tests     \\    (many, fast, focused)
```

**2. Unit Tests** (pytest):
- Test each agent's task routing
- Test LLM provider selection
- Test memory operations
- Test state manager operations
- Mocking: LLM calls, database, external APIs

**3. Integration Tests**:
- API endpoint tests (FastAPI TestClient)
- Agent ↔ database interaction
- Message bus round-trip
- Full task execution flow (with mocked LLM)

**4. E2E Tests**:
- Start server, hit health endpoint
- Create task flow via API
- Verify agent state changes
- Test SSE streaming

**5. Load Testing** (locust):
```python
class HackBotUser(HttpUser):
    @task
    def health_check(self):
        self.client.get("/health")
    @task
    def get_agents(self):
        self.client.get("/api/agents")
```

**6. Test Configuration**:
- conftest.py with fixtures: test DB, mock LLM, test agents
- pytest.ini: markers, coverage config
- GitHub Actions integration
- Coverage badge in README

**7. Quality Gates**:
- Minimum 60% coverage
- No tests skipped in CI
- Performance regression detection
- Security test suite

Provide pytest config and example test files."""
        )

        await self.memory.remember("testing_config", result[:600], category="testing")
        await self.send_message("cto", f"Testing Infrastructure: {result[:300]}", "report")
        return result

    # ── SSL/DNS Management ─────────────────────────────────
    async def _manage_ssl_dns(self, description: str) -> str:
        """Manage SSL certificates, DNS, and domain configuration."""
        result = await self.think(
            f"""SSL/DNS task: {description}

**1. SSL/TLS Setup**:
- Let's Encrypt with certbot (auto-renewal)
- Or Cloudflare SSL (simpler, free)
- Force HTTPS redirects
- HSTS header enabled
- TLS 1.2+ only

**2. DNS Configuration**:
- A record → server IP
- CNAME www → root domain
- MX records (if email needed)
- TXT records (SPF, DKIM for email)
- CAA record (authorized CAs)

**3. CDN Setup** (Cloudflare):
- Proxy through Cloudflare
- Cache static assets (CSS, JS, images)
- DDoS protection (free tier)
- Firewall rules (block bad bots)
- Page rules for caching

**4. Certificate Monitoring**:
- Auto-renewal cron (certbot renew)
- Expiry alerts (14 days before)
- Certificate transparency monitoring

**5. Security Headers** (nginx):
```
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header X-Content-Type-Options "nosniff";
add_header X-Frame-Options "DENY";
add_header Content-Security-Policy "default-src 'self'";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()";
```

Provide implementation commands and configs."""
        )

        await self.memory.remember("ssl_dns_config", result[:400], category="ssl")
        return result

    # ── Performance Engineering ─────────────────────────────
    async def _performance_engineering(self, description: str) -> str:
        """Profile, optimize, and load test the application."""
        result = await self.think(
            f"""Performance engineering task: {description}

Product: {settings.product_name} — FastAPI + Python

**1. Application Profiling**:
- Endpoint response times (add middleware):
```python
@app.middleware("http")
async def timing_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-Response-Time"] = f"{{duration:.3f}}s"
    return response
```
- Memory profiling (tracemalloc)
- CPU profiling (cProfile/py-spy)
- Database query profiling

**2. Optimization Targets**:
| Metric | Current | Target |
|--------|---------|--------|
| Health check | ? | <50ms |
| API endpoints | ? | <200ms |
| Page load | ? | <1s |
| LLM calls | ? | <5s (provider dependent) |
| Memory usage | ? | <256MB |

**3. Common Optimizations**:
- Enable SQLite WAL mode
- Connection pooling
- Response compression (gzip middleware)
- Static file caching headers
- Async everywhere (already using aio)
- Lazy imports for heavy modules

**4. Load Testing Plan**:
- Baseline: Current request/sec capacity
- Target: 100 concurrent users
- Tool: locust or k6
- Scenarios: normal load, peak load, spike test

**5. Frontend Performance**:
- Minimize CSS/JS
- Compress images/sprites
- Enable browser caching
- Lazy load non-critical resources

**6. Performance Budget**:
- Set limits and alert when exceeded
- Track over time (trend dashboard)

Provide specific implementation code and benchmarks."""
        )

        await self.memory.remember("perf_status", result[:600], category="performance")
        return result

    # ── Compliance & Auditing ──────────────────────────────
    async def _compliance_audit(self, description: str) -> str:
        """Run compliance checks and maintain audit records."""
        result = await self.think(
            f"""Compliance audit task: {description}

Product: {settings.product_name} — AI pentesting chatbot (security tool!)

**1. OWASP Top 10 Checklist**:
- [ ] A01: Broken Access Control — API auth, endpoint protection
- [ ] A02: Cryptographic Failures — HTTPS, secrets handling
- [ ] A03: Injection — Input validation, parameterized queries
- [ ] A04: Insecure Design — Threat modeling done?
- [ ] A05: Security Misconfiguration — Default configs changed?
- [ ] A06: Vulnerable Components — Dependency audit
- [ ] A07: Auth Failures — Session management, API keys
- [ ] A08: Data Integrity — Update mechanism security
- [ ] A09: Logging — Security events logged?
- [ ] A10: SSRF — External request validation

**2. Open Source Compliance**:
- LICENSE file present and correct
- All dependencies license-compatible
- No copyleft violations
- Attribution where required
- NOTICE file if needed

**3. Data Handling**:
- What data do we collect?
- Where is it stored?
- Who has access?
- Retention policy
- Deletion capability
- Privacy policy needed?

**4. Access Control Audit**:
- GitHub repo access review
- API key rotation schedule
- SSH key management
- Service account inventory

**5. Audit Log**:
- What events are logged?
- What should be logged?
- Retention period
- Tamper protection

Rate each area: ✅ Compliant / ⚠️ Partial / ❌ Non-Compliant"""
        )

        await self.memory.remember("compliance_status", result[:600], category="compliance")
        await self.send_message("cto", f"Compliance Audit: {result[:300]}", "report")
        return result

    # ── Cost Management ────────────────────────────────────
    async def _cost_management(self, description: str) -> str:
        """Monitor and optimize cloud and service costs."""
        result = await self.think(
            f"""Cost management task: {description}

Product: {settings.product_name}
Stage: Early startup, bootstrap budget

**1. Current Cost Breakdown**:
| Service | Estimated Monthly Cost |
|---------|----------------------|
| VPS (DigitalOcean 2GB) | $12 |
| Domain | ~$1 (annual /12) |
| Cloudflare | $0 (free tier) |
| GitHub | $0 (free for public) |
| LLM API (OpenAI/Anthropic) | Variable |
| Monitoring | $0 (self-hosted) |
| **Total** | **~$15 + LLM costs** |

**2. LLM Cost Optimization**:
- Use cheaper models for routine tasks (GPT-3.5 vs GPT-4)
- Cache common responses
- Batch requests where possible
- Set hard spending limits per provider
- Monitor token usage per agent
- Consider local models (Ollama) for dev/testing

**3. Infrastructure Cost Optimization**:
- Right-size server (don't over-provision)
- Use spot/preemptible instances for CI
- Clean up unused resources
- Compress and optimize storage
- CDN for static assets (reduce bandwidth)

**4. Budget Alerts**:
- Alert at 80% of monthly budget
- Daily cost tracking
- Per-service breakdown
- Anomaly detection (unexpected spikes)

**5. Scaling Cost Projection**:
- 100 users: ~$20/mo
- 1,000 users: ~$50-100/mo
- 10,000 users: ~$200-500/mo
- Key cost driver: LLM API calls

**6. Free Tier Maximization**:
- GitHub Actions: 2,000 min/mo free
- Cloudflare: Free CDN, DNS, SSL
- UptimeRobot: 50 monitors free
- Sentry: 5K errors/mo free"""
        )

        await self.memory.remember("cost_analysis", result[:600], category="cost")
        await self.send_message("cto", f"Cost Analysis: {result[:300]}", "report")
        return result

    # ── Documentation ──────────────────────────────────────
    async def _write_documentation(self, description: str) -> str:
        """Write and maintain technical documentation."""
        result = await self.think(
            f"""Documentation task: {description}

Product: {settings.product_name}

**1. Essential Docs** (priority order):
- README.md — Project overview, quick start, features
- CONTRIBUTING.md — How to contribute, code style, PR process
- ARCHITECTURE.md — System design, component diagram, data flow
- DEPLOYMENT.md — How to deploy, environment setup
- API.md — API endpoints (auto-gen from FastAPI /docs)

**2. Runbooks** (for IT/ops):
- How to deploy a new version
- How to rollback
- How to handle incidents
- How to rotate secrets
- How to restore from backup
- How to scale up/down

**3. README Template**:
```markdown
# {settings.product_name}
> One-line description

## Features
- Feature 1
- Feature 2

## Quick Start
git clone / docker-compose up / done

## Architecture
Brief overview + diagram link

## Contributing
Link to CONTRIBUTING.md

## License
MIT
```

**4. Inline Documentation Standards**:
- Docstrings on all public functions
- Type hints everywhere
- Comments for non-obvious logic
- No commented-out code

**5. Documentation Maintenance**:
- Review docs on every release
- Automated link checking
- Version docs with code
- Changelog maintenance (CHANGELOG.md)

Write the actual content for the most needed document."""
        )

        return result

    # ── Automation Builder ─────────────────────────────────
    async def _build_automation(self, description: str) -> str:
        """Build automation scripts and tools."""
        result = await self.think(
            f"""Automation task: {description}

Product: {settings.product_name}
Stack: Python, Docker, GitHub Actions, Linux

Build automation for:

**1. Release Automation**:
```bash
#!/bin/bash
# release.sh — automated release process
set -e
VERSION=$1
echo "Releasing v$VERSION..."
# 1. Run tests
pytest --cov=. -v
# 2. Build Docker image
docker build -t hackbot:$VERSION .
# 3. Tag and push
git tag v$VERSION
git push origin v$VERSION
# 4. Push Docker image
docker push ghcr.io/yashab-cyber/hackbot:$VERSION
docker push ghcr.io/yashab-cyber/hackbot:latest
echo "Released v$VERSION ✅"
```

**2. Health Check Script**:
```bash
#!/bin/bash
# healthcheck.sh — verify all systems operational
HEALTH=$(curl -sf http://localhost:8000/health)
if [ $? -ne 0 ]; then
    echo "CRITICAL: Health check failed!"
    # Send alert
    exit 1
fi
echo "OK: $HEALTH"
```

**3. Backup Automation**:
- Cron: `0 */6 * * * /opt/hackbot/backup.sh`
- Copies DB, rotates old backups, syncs to cloud

**4. Log Rotation**:
- logrotate config for application logs
- Compress old logs
- Retention: 30 days

**5. Dependency Update Automation**:
- Weekly: `pip-audit` + `pip install --upgrade`
- Auto-PR for dependency updates
- CI validates before merge

**6. Environment Setup Script**:
```bash
#!/bin/bash
# setup.sh — one-command dev environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
echo "Ready! Run: uvicorn server:app --reload"
```

Provide production-ready scripts."""
        )

        await self.memory.remember("automation_scripts", result[:400], category="automation")
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
        """IT generates an infrastructure & operations executive report."""
        tasks = await state_manager.get_agent_tasks(self.agent_id, limit=30)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_tasks = [t for t in tasks if t.get("started_at", "").startswith(today)]

        infra = await self.memory.recall("infra_status", "infrastructure")
        security = await self.memory.recall("security_status", "security")
        cicd = await self.memory.recall("cicd_status", "cicd")

        report = await self.think(
            f"""Generate the IT daily operations report.

## IT Tasks Today
{json.dumps(today_tasks, indent=2) if today_tasks else 'No IT tasks today.'}

## Infrastructure Status
{infra[:300] if infra else 'Not assessed yet.'}

## Security Status
{security[:300] if security else 'Not audited yet.'}

## CI/CD Status
{cicd[:200] if cicd else 'Not configured yet.'}

Write a concise IT ops report:
1. IT activities completed today
2. Infrastructure health: 🟢 Healthy / 🟡 Degraded / 🔴 Down
3. Security posture: Strong / Moderate / Weak
4. CI/CD pipeline status
5. Active incidents (if any)
6. Cost status (on budget / over)
7. Tomorrow's IT priorities (top 3)
8. Risks or blockers for CTO attention

Under 250 words. Be specific and technical."""
        )

        await state_manager.save_daily_report(self.agent_id, report)
        return f"**IT Infrastructure & Operations Report**\n{report}"
