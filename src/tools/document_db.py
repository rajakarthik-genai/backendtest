"""
Wrapper around MongoDB for quick patient-centric queries usable by agents.

Heavy CRUD lives in src/db/mongo_db.py – this module provides lightweight,
human-readable helpers that return strings safe for LLM context.
"""

from __future__ import annotations

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from src.utils.logging import logger

_client: MongoClient | None = None
_db = None


def _init(uri: str):
    """Called from tools.__init__.init_mongo once at startup."""
    global _client, _db
    if _client:
        return
    _client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    try:
        _client.admin.command("ping")
        logger.info("tools.document_db – Mongo connected.")
    except Exception as exc:
        logger.error("tools.document_db – Mongo connection error: %s", exc)
    # Use DB name from URI or fallback
    db_name = uri.rsplit("/", 1)[-1] or "digital_twin"
    _db = _client[db_name]


# --------------------------------------------------------------------------- #
# Helper getters – return short descriptive strings (LLM-friendly)
# --------------------------------------------------------------------------- #
def get_patient_profile(user_id: str) -> str:
    coll = _db["patients"]
    doc = coll.find_one({"_id": ObjectId(user_id)}) or coll.find_one({"user_id": user_id})
    if not doc:
        return "Patient profile not found."
    name = doc.get("first_name", "") + " " + doc.get("last_name", "")
    age = doc.get("age", "N/A")
    gender = doc.get("gender", "N/A")
    conds = ", ".join(doc.get("conditions", [])) or "none"
    return f"{name.strip()} | Age: {age} | Gender: {gender} | Known conditions: {conds}"


def get_patient_record(user_id: str, record_type: str) -> str:
    """
    record_type examples: 'labs', 'imaging', 'reports'.
    Returns newest record as formatted string or message if none.
    """
    coll = _db.get(record_type)
    if not coll:
        return f"No collection '{record_type}'."
    doc = coll.find_one(
        {"patient_id": {"$in": [user_id, ObjectId(user_id)]}},
        sort=[("timestamp", -1)],
    )
    if not doc:
        return f"No {record_type} records for patient."
    # Remove noisy fields
    doc.pop("_id", None)
    doc.pop("patient_id", None)
    lines = [f"{k}: {v}" for k, v in doc.items()]
    return "; ".join(lines)
