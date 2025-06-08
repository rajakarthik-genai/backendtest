"""
Facade that exposes high-level helpers expected elsewhere in the codebase.

Functions exported:
    add_message_to_history   (alias of STM.add)
    get_conversation_history (alias of STM.history)
    get_last_user_question   (alias of STM.last_user_question)
    get_long_term_memory     (alias of LTM.get)
    update_long_term_memory  (alias of LTM.update)
"""
from typing import List, Dict, Optional
from .short_term import add as _stm_add, history as _stm_hist, \
                         last_user_question as _stm_last
from .long_term import get as _ltm_get, update as _ltm_update

# ---- STM passthrough -----------------------------------------------------
def add_message_to_history(user_id: str, doctor_id: str,
                           conv_id: str, role: str, text: str) -> None:
    _stm_add(user_id, doctor_id, conv_id, role, text)

def get_conversation_history(user_id: str, doctor_id: str,
                             conv_id: str, limit: int = 20) -> List[Dict]:
    hist = _stm_hist(user_id, doctor_id, conv_id)
    return hist[-limit:]

def get_last_user_question(user_id: str, doctor_id: str,
                           conv_id: str) -> Optional[str]:
    return _stm_last(user_id, doctor_id, conv_id)

# ---- LTM passthrough -----------------------------------------------------
def get_long_term_memory(user_id: str) -> Dict:
    return _ltm_get(user_id) or {}

def update_long_term_memory(user_id: str, new_data: Dict) -> None:
    _ltm_update(user_id, new_data)
