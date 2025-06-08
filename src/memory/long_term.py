"""
Long-term memory (LTM)
Persistent patient summary keyed only by user_id.

Key pattern:  ltm:<user_id>
"""
from typing import Dict, Optional
from .redis_client import client as R, dumps, loads

def _key(uid: str) -> str: return f"ltm:{uid}"

def get(uid: str) -> Optional[Dict]:
    return loads(R.get(_key(uid)))

def set(uid: str, summary: Dict) -> None:
    R.set(_key(uid), dumps(summary))

def update(uid: str, patch: Dict) -> None:
    current = get(uid) or {}
    for k, v in patch.items():
        if isinstance(v, list):
            cur = current.get(k, [])
            current[k] = list({*cur, *v})   # merge unique
        else:
            current[k] = v
    set(uid, current)

def clear(uid: str) -> None:
    R.delete(_key(uid))
