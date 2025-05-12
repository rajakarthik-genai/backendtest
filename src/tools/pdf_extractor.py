# tools/pdf_extractor.py

import pdfplumber, fitz, io, json, logging, os, tempfile
from PIL import Image
from openai import OpenAI
openai_client = OpenAI()
VISION_MODEL = "gpt-4o-mini"   # vision-capable :contentReference[oaicite:3]{index=3}
log = logging.getLogger(__name__)

def _plumber_text(path):
    txt, tables = "", []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            txt += (p.extract_text() or "")
            if (t:=p.extract_table()):
                hdr,*rows=t; tables.append([dict(zip(hdr,r)) for r in rows])
    return txt.strip(), tables

def _vision_ocr(images):
    prompt = ("Extract the full text AND metadata as JSON: "
              "{metadata:{doctor_name, hospital_name, test_type, modality, report_date}, "
              "text:\"...\"}.  Use null for unknowns.")
    resp = openai_client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{"role":"system","content":prompt},
                  {"role":"user","content":"process"}],
        images=images )
    return json.loads(resp.choices[0].message.content)

def extract(path)->tuple[str,dict]:
    """Return (text, metadata) – use pdfplumber first, fallback to GPT-vision."""
    text, meta = "", {}
    text, _ = _plumber_text(path)
    if text:
        meta = {}            # pdfplumber found machine text – minimal meta
        return text, meta
    # fallback – render pages & call GPT vision
    doc = fitz.open(path)
    imgs=[]
    for pg in doc:
        pix = pg.get_pixmap(dpi=250)
        imgs.append(pix.tobytes("png"))
    data = _vision_ocr(imgs)
    return data.get("text",""), data.get("metadata",{})
