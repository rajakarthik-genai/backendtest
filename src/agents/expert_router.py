"""
Pick specialists from keywords; build CrewAI crew; return ordered specialist list.
"""

from typing import List
from src.utils.logging import logger
from . import (
    cardiologist_agent,
    general_physician_agent,
    orthopedist_agent,
    neurologist_agent,
)

_KEYWORDS = {
    "cardiologist": ["heart", "chest pain", "cardiac", "palpitation", "angina"],
    "orthopedist": ["bone", "joint", "fracture", "knee", "elbow", "ankle", "sprain"],
    "neurologist": ["brain", "nerve", "headache", "seizure", "memory"],
}

_MAPPING = {
    "cardiologist": cardiologist_agent.handle_query,
    "orthopedist": orthopedist_agent.handle_query,
    "neurologist": neurologist_agent.handle_query,
    "general_physician": general_physician_agent.handle_query,
}


def choose_specialists(question: str) -> List[str]:
    """Return list of role keys best matching the question."""
    q = question.lower()
    chosen = []
    for role, kws in _KEYWORDS.items():
        if any(kw in q for kw in kws):
            chosen.append(role)
    if not chosen:
        chosen.append("general_physician")
    return chosen


def get_handlers(role_names: List[str]):
    """Utility to map role names to handler callables."""
    return [_MAPPING[r] for r in role_names]
