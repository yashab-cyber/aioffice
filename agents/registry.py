"""Agent registry — single source of truth for all agents."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base_agent import BaseAgent

logger = logging.getLogger("aioffice")

# Registry populated at startup
AGENT_REGISTRY: dict[str, "BaseAgent"] = {}

# Agent metadata (role descriptions, dependencies, team assignments)
AGENT_METADATA: dict[str, dict] = {}

# Team structure
TEAMS = {
    "leadership": ["ceo", "cto", "cmo", "cxo"],
    "growth": ["marketing", "sales"],
    "operations": ["hr", "it"],
    "community": ["discord"],
}


def register_all() -> dict[str, "BaseAgent"]:
    """Instantiate and register every agent."""
    from agents.ceo import CEOAgent
    from agents.cto import CTOAgent
    from agents.cmo import CMOAgent
    from agents.cxo import CXOAgent
    from agents.marketing_team import MarketingAgent
    from agents.sales_team import SalesAgent
    from agents.hr import HRAgent
    from agents.it_team import ITAgent
    from agents.discord_team import DiscordAgent

    agents = [
        CEOAgent(),
        CTOAgent(),
        CMOAgent(),
        CXOAgent(),
        MarketingAgent(),
        SalesAgent(),
        HRAgent(),
        ITAgent(),
        DiscordAgent(),
    ]
    for agent in agents:
        AGENT_REGISTRY[agent.agent_id] = agent
        AGENT_METADATA[agent.agent_id] = {
            "role": agent.role,
            "description": agent.description,
            "team": _get_team(agent.agent_id),
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
    logger.info(f"Registered {len(AGENT_REGISTRY)} agents: {', '.join(AGENT_REGISTRY.keys())}")
    return AGENT_REGISTRY


def _get_team(agent_id: str) -> str:
    for team, members in TEAMS.items():
        if agent_id in members:
            return team
    return "unassigned"


def get_team_members(team: str) -> list[str]:
    """Get agent IDs for a team."""
    return TEAMS.get(team, [])


def get_agent(agent_id: str) -> "BaseAgent | None":
    """Get an agent by ID."""
    return AGENT_REGISTRY.get(agent_id)


async def get_all_health() -> dict[str, dict]:
    """Run health checks on all agents."""
    results = {}
    for aid, agent in AGENT_REGISTRY.items():
        try:
            results[aid] = await agent.health_check()
        except Exception as e:
            results[aid] = {"agent_id": aid, "healthy": False, "error": str(e)}
    return results


def get_registry_info() -> dict:
    """Return full registry metadata."""
    return {
        "total_agents": len(AGENT_REGISTRY),
        "agents": {
            aid: {
                **AGENT_METADATA.get(aid, {}),
                "status": agent.status,
                "current_task": agent._current_task,
            }
            for aid, agent in AGENT_REGISTRY.items()
        },
        "teams": TEAMS,
    }
