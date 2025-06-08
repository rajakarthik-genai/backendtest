from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from src.agents.ingestion_agent import ingest_pdf
from src.db import mongo_db
from datetime import datetime, timezone
import aiofiles, tempfile, os, asyncio

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/", response_class=StreamingResponse)
async def upload(user_id:str, file:UploadFile=File(...)):
    tmp = tempfile.NamedTemporaryFile(delete=False,suffix=".pdf")
    async with aiofiles.open(tmp.name,'wb') as f:
        while chunk:=await file.read(1024*1024):
            await f.write(chunk)
    async def events():
        yield "data: file saved\n\n"
        await mongo_db.save_ingest_log({"user_id":user_id,"file":file.filename,"status":"saved","ts":datetime.now(timezone.utc)})
        try:
            await ingest_pdf(user_id,tmp.name)
            yield "data: ingestion complete\n\n"
        except Exception as e:
            yield f"data: error {e}\n\n"
    return StreamingResponse(events(),media_type="text/event-stream")
