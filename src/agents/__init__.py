"""
Import-shortcut so other packages can do:

    from agents import cardiologist_agent

and access its functions (e.g., .handle_query).

Nothing is executed eagerly except prompt loading.
"""
from importlib import import_module as _imp

cardiologist_agent      = _imp("agents.cardiologist_agent")
general_physician_agent = _imp("agents.general_physician_agent")
orthopedist_agent       = _imp("agents.orthopedist_agent")
neurologist_agent       = _imp("agents.neurologist_agent")

# Orchestrator & aggregator are used by API layer
from agents.orchestrator_agent import orchestrator_agent
from agents.aggregator_agent   import aggregator_agent

__all__ = [
    "cardiologist_agent",
    "general_physician_agent",
    "orthopedist_agent",
    "neurologist_agent",
    "orchestrator_agent",
    "aggregator_agent",
]
