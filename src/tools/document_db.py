"""
MongoDB helper for patient profiles & records.
"""
from __future__ import annotations
from typing import Any
from pymongo import MongoClient
from utils.logging import logger

_client: MongoClient | None = None
_db = None


def init_mongo(uri: str) -> None:
    """
    Initialise Mongo client and cache default DB.
    """
    global _client, _db
    if _client:
        return
    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        _db = _client.get_database()
        _client.admin.command("ping")
        logger.info(f"Mongo connected to {uri}")
    except Exception as exc:
        logger.error(f"Mongo init error: {exc}")


def _coll(name: str):
    if _db is None:
        raise RuntimeError("Mongo not initialised.")
    return _db[name]


def get_patient_profile(user_id: str) -> str:
    """
    Return a short, human-readable summary of patient profile (or empty str).
    """
    try:
        doc = _coll("patients").find_one({"user_id": user_id})
        if not doc:
            return ""
        name = doc.get("name", "Unknown")
        age = doc.get("age", "N/A")
        conditions = ", ".join(doc.get("conditions", [])) or "none"
        return f"{name}, age {age}; conditions: {conditions}"
    except Exception as exc:
        logger.error(f"Mongo get_patient_profile error: {exc}")
        return ""


def get_patient_record(user_id: str, record_type: str) -> str:
    """
    Fetch a specific record type (collection) for the user and return pretty JSON.
    """
    try:
        col = _coll(record_type)
        rec: dict[str, Any] | None = col.find_one({"user_id": user_id})
        if not rec:
            return f"No {record_type} records."
        rec.pop("_id", None)
        rec.pop("user_id", None)
        # Simple pretty str
        return "; ".join(f"{k}: {v}" for k, v in rec.items())
    except Exception as exc:
        logger.error(f"Mongo get_patient_record error: {exc}")
        return ""
