"""Agent registry — single source of truth for all agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base_agent import BaseAgent

# Registry populated at startup
AGENT_REGISTRY: dict[str, "BaseAgent"] = {}


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
    return AGENT_REGISTRY
