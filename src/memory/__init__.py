"""
Deprecated import shim – forwards to `src.chat` implementation.

Existing code can still:
    from src.memory import memory_manager
"""

from .memory_manager import (
    add_message_to_history,
    get_conversation_history,
    get_last_user_question,
    get_long_term_memory,
    update_long_term_memory,
)
