"""
/upload – accepts PDF/image and queues ingestion task.
"""

import os, shutil, tempfile
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Query, BackgroundTasks, HTTPException
from bson import ObjectId
from src.db.mongo_db import MongoDBClient
from src.agents.ingestion_agent import ingest_pdf  # async task
from src.utils.logging import logger
from src.config.settings import settings

router = APIRouter(prefix="/upload", tags=["upload"])
mongo = MongoDBClient(settings.mongo_uri, settings.mongo_db_name)


@router.post("/")
async def upload(
    background_tasks: BackgroundTasks,
    user_id: str = Query(...),
    file: UploadFile = File(...),
):
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in (".pdf", ".png", ".jpg", ".jpeg"):
        raise HTTPException(400, detail="Only PDF or image files are accepted.")

    # Save to a temp file
    tmp_dir = tempfile.mkdtemp(prefix="ingest_")
    save_path = os.path.join(tmp_dir, file.filename)
    with open(save_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    # Insert ingest log
    ingest_id = mongo.collection.insert_one(
        {
            "patient_id": user_id,
            "file_name": file.filename,
            "path": save_path,
            "status": "queued",
            "timestamp": datetime.now(timezone.utc),
        }
    ).inserted_id
    # Background ingestion
    background_tasks.add_task(ingest_pdf, user_id=user_id, file_path=save_path, ingest_log_id=str(ingest_id))
    logger.info("File %s queued for ingestion id=%s", file.filename, ingest_id)
    return {"ingest_id": str(ingest_id), "status": "queued"}
