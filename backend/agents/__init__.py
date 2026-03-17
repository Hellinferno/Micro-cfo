"""
MicroCFO Agents Module
AI-powered agents for financial operations
"""

from backend.agents.visual_auditor import initialize_agent_a
from backend.agents.legal_sentinel import initialize_agent_b
from backend.agents.subsidy_hunter import initialize_agent_c
from backend.agents.negotiator import initialize_agent_d
from backend.agents.orchestrator import initialize_orchestrator


def initialize_agents():
    """Initialize all AI agents"""
    print("Initializing MicroCFO Agents...")
    
    # Initialize each agent
    agent_a_status = initialize_agent_a()
    agent_b_status = initialize_agent_b()
    agent_c_status = initialize_agent_c()
    agent_d_status = initialize_agent_d()
    orchestrator_status = initialize_orchestrator()
    
    # Report status
    print("\n=== Agent Initialization Status ===")
    print(f"Agent A (Visual Auditor): {'✓' if agent_a_status else '✗'}")
    print(f"Agent B (Legal Sentinel): {'✓' if agent_b_status else '✗'}")
    print(f"Agent C (Subsidy Hunter): {'✓' if agent_c_status else '✗'}")
    print(f"Agent D (Negotiator): {'✓' if agent_d_status else '✗'}")
    print(f"Orchestrator: {'✓' if orchestrator_status else '✗'}")
    print("====================================\n")
    
    return all([
        agent_a_status,
        agent_b_status,
        agent_c_status,
        agent_d_status,
        orchestrator_status
    ])


__all__ = [
    "initialize_agents",
    "initialize_agent_a",
    "initialize_agent_b",
    "initialize_agent_c",
    "initialize_agent_d",
    "initialize_orchestrator"
]
