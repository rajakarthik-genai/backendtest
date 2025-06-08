"""
Short-term memory (STM)
Keeps a rolling window of the last N chat messages *per conversation*.

Key pattern:  stm:<user_id>:<doctor_id>:<conv_id>
"""
from datetime import datetime
from typing import List, Dict
from .redis_client import client as R, dumps, loads

MAX_CTX = 20          # keep last 20 messages per conversation

def _key(uid: str, did: str, cid: str) -> str:
    return f"stm:{uid}:{did}:{cid}"

def add(uid: str, did: str, cid: str, role: str, text: str) -> None:
    entry = dumps({"role": role, "content": text,
                   "timestamp": datetime.utcnow().isoformat()})
    R.rpush(_key(uid, did, cid), entry)
    R.ltrim(_key(uid, did, cid), -MAX_CTX, -1)

def history(uid: str, did: str, cid: str) -> List[Dict]:
    raw = R.lrange(_key(uid, did, cid), 0, -1)
    return [loads(x) for x in raw]

def last_user_question(uid: str, did: str, cid: str) -> str | None:
    for item in reversed(history(uid, did, cid)):
        if item["role"] == "user":
            return item["content"]
    return None

def clear(uid: str, did: str, cid: str) -> None:
    R.delete(_key(uid, did, cid))
