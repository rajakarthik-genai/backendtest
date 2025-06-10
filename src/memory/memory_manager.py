"""
Back-compat manager that simply re-exports chat.history helpers.
"""

from typing import Dict, List, Any, Optional
from src.chat.history import ChatHistory as _H

# STM helpers
add_message_to_history = _H.add_msg
get_conversation_history = _H.recent
get_last_user_question = _H.last_question

# LTM helpers
get_long_term_memory = _H.user_profile
update_long_term_memory = _H.update_profile
