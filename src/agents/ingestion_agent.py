# agents/ingestion_agent.py

from src.tools import pdf_extractor
from src.db import mongo_db, neo4j_db, milvus_db
import openai, json, os, asyncio, logging
GPT_MODEL = os.getenv("GPT_MODEL","gpt-4o-mini")
log = logging.getLogger(__name__)

async def ingest_pdf(user_id:str, path:str):
    # 1. extraction
    raw, meta = pdf_extractor.extract(path)
    report_id = await mongo_db.save_full_report(user_id, raw, meta)
    # 2. GPT entity-insight
    prompt = ("Identify labs, vitals, meds, injuries, organs, conditions, treatments "
              "IN JSON keys exactly.  Infer conditions from abnormal values.")
    resp = openai.chat.completions.create(
        model=GPT_MODEL, temperature=0.0,
        messages=[{"role":"system","content":prompt},
                  {"role":"user","content":raw[:16000]}])
    struct = json.loads(resp.choices[0].message.content)
    date = meta.get("report_date")
    # 3. store each entity (examples)
    for lab in struct.get("lab_results",[]):
        lab_id = await mongo_db.save_lab_result(user_id, report_id, lab)
        await neo4j_db.merge_lab(user_id, lab, date)
        for cond in struct.get("conditions",[]):
            await neo4j_db.link_lab_condition(user_id, lab["name"], date, cond)
    for cond in struct.get("conditions",[]):
        await mongo_db.save_condition(user_id, report_id, cond)
        await neo4j_db.merge_condition(user_id, cond)
    for med in struct.get("medications",[]):
        await mongo_db.save_medication(user_id, report_id, med)
        await neo4j_db.merge_medication(user_id, med)
        for cond in struct.get("conditions",[]):     # link med→condition
            await neo4j_db.link_med_condition(med, cond)
    for inj in struct.get("injuries",[]):
        await mongo_db.save_injury(user_id, report_id, inj)
        await neo4j_db.merge_injury(user_id, inj, date)
        if meta.get("doctor_name"):
            await neo4j_db.link_injury_doctor(inj["description"], meta["doctor_name"])
    # 4. vectors by section (only if raw text exists)
    if raw:
        for idx,sec in enumerate(milvus_db.split_sections(raw)):
            await milvus_db.upsert_vector(user_id, report_id, date,
                                          sec["header"], sec["body"], idx)
    # 5. timeline event
    await mongo_db.save_event({"user_id":user_id,"report_id":report_id,
                               "type":meta.get("test_type","Report"),
                               "date":date})
