"""
Expose top-level agent handles so other modules can import:

    from src.agents import orchestrator_agent

and call:

    await orchestrator_agent.handle_request(...)
"""
from .orchestrator_agent import orchestrator_agent  # noqa: F401
from .aggregator_agent import aggregator_agent   # noqa: F401
from .cardiologist_agent import cardiologist_agent  # noqa: F401
from .general_physician_agent import general_physician_agent  # noqa: F401
from .orthopedist_agent import orthopedist_agent  # noqa: F401
from .neurologist_agent import neurologist_agent  # noqa: F401