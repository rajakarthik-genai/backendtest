"""
High-level convenience wrapper that combines STM and LTM for agents.

Agents / endpoints import:

    from src.chat.history import ChatHistory
"""

from typing import Dict, List, Any
from .short_term import ShortTermMemory as STM
from .long_term import LongTermMemory as LTM


class ChatHistory:
    """Facade exposing a minimal API for orchestrator & agents."""

    # --- STM --------------------------------------------------------------
    @staticmethod
    def add_msg(user_id: str, doctor_id: str, conv_id: str, role: str, text: str):
        STM.add(user_id, doctor_id, conv_id, role, text)

    @staticmethod
    def recent(user_id: str, doctor_id: str, conv_id: str, limit: int = 20) -> List[Dict]:
        return STM.history(user_id, doctor_id, conv_id)[-limit:]

    @staticmethod
    def last_question(user_id: str, doctor_id: str, conv_id: str) -> str | None:
        return STM.last_user_msg(user_id, doctor_id, conv_id)

    @staticmethod
    def clear_session(user_id: str, doctor_id: str, conv_id: str):
        STM.clear(user_id, doctor_id, conv_id)

    # --- LTM --------------------------------------------------------------
    @staticmethod
    def user_profile(user_id: str) -> Dict[str, Any]:
        return LTM.get(user_id)

    @staticmethod
    def update_profile(user_id: str, new_data: Dict[str, Any]):
        LTM.update(user_id, new_data)
