from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, File, UploadFile, Query, HTTPException

from src.db import mongo_db
from src.agents.ingestion_agent import run_ingestion_agent
from src.utils.logging import log

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/")
async def upload_file(
    background_tasks: BackgroundTasks,
    user_id: str = Query(...),
    file: UploadFile = File(...),
):
    if not file.filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(400, detail="Only PDF/Image accepted")

    save_path = f"/tmp/{datetime.utcnow().timestamp()}_{file.filename}"
    with open(save_path, "wb") as out:
        out.write(await file.read())

    log_id = await mongo_db.save_ingest_log(
        {
            "user_id": user_id,
            "file": file.filename,
            "path": save_path,
            "status": "pending",
            "ts": datetime.now(timezone.utc),
        }
    )
    background_tasks.add_task(
        run_ingestion_agent, user_id=user_id, filepath=save_path, ingest_log_id=log_id
    )
    return {"ingest_id": log_id, "status": "queued"}
