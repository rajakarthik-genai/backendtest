"""
Import-shortcut so other packages can do:

    from agents import cardiologist_agent

and access its functions (e.g., .handle_query).

Nothing is executed eagerly except prompt loading.
"""
from importlib import import_module as _imp

cardiologist_agent      = _imp("src.agents.cardiologist_agent")
general_physician_agent = _imp("src.agents.general_physician_agent")
orthopedist_agent       = _imp("src.agents.orthopedist_agent")
neurologist_agent       = _imp("src.agents.neurologist_agent")

from src.agents.aggregator_agent   import aggregator_agent
from src.agents.orchestrator_agent import OrchestratorAgent

__all__ = [
    "cardiologist_agent",
    "general_physician_agent",
    "orthopedist_agent",
    "neurologist_agent",
    "OrchestratorAgent",
    "aggregator_agent",
]
