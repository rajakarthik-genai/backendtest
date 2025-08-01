# Dependencies: PyMuPDF (fitz), pytesseract, Pillow (PIL), numpy (for PaddleOCR usage), regex, datetime
import fitz  # PyMuPDF for PDF reading
import pytesseract
from PIL import Image
import numpy as np
import re
from datetime import datetime

class PDFExtractor:
    """
    Service for extracting text and structured data from medical PDFs (scanned or digital).
    Uses OCR (Tesseract or PaddleOCR) for scanned pages and NLP heuristics for data extraction.
    """
    def __init__(self, ocr_engine: str = "tesseract"):
        """
        Initialize PDFExtractor.
        ocr_engine: 'tesseract' or 'paddle' to specify OCR engine for scanned PDFs.
        """
        self.ocr_engine = ocr_engine.lower()
        self._paddle_ocr = None  # will hold PaddleOCR instance if used
    
    def extract_text(self, file_path: str):
        """
        Extract text from each page of the PDF.
        For digital text PDFs, uses PyMuPDF text extraction.
        For scanned PDFs (no text), uses OCR via the specified engine.
        Returns a list of page texts.
        """
        doc = fitz.open(file_path)
        pages_text = []
        for page in doc:
            text = page.get_text().strip()
            if text:
                # If the page has text content, use it directly
                pages_text.append(text)
            else:
                # If no text found, fall back to OCR on the page image
                pix = page.get_pixmap(dpi=300)
                mode = "RGB"  # use RGB for OCR
                if pix.alpha:  # remove alpha channel if present
                    mode = "RGBA"
                img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
                ocr_text = ""
                if self.ocr_engine == "paddle":
                    # Use PaddleOCR for OCR
                    try:
                        from paddleocr import PaddleOCR
                    except ImportError:
                        raise RuntimeError("PaddleOCR not installed; install paddleocr or use Tesseract engine.")
                    if self._paddle_ocr is None:
                        # Initialize PaddleOCR once
                        self._paddle_ocr = PaddleOCR(use_angle_cls=False, lang='en')
                    # Convert image to numpy array (BGR format for PaddleOCR)
                    img_array = np.array(img.convert("RGB"))[:, :, ::-1]  # RGB to BGR
                    ocr_result = self._paddle_ocr.ocr(img_array, cls=False)
                    for line in ocr_result:
                        ocr_text += line[1][0] + "\n"
                else:
                    # Default to Tesseract OCR
                    ocr_text = pytesseract.image_to_string(img)
                pages_text.append(ocr_text.strip())
        doc.close()
        return pages_text
    
    def parse_patient_info(self, text: str):
        """
        Extract basic patient details (name, id, age, gender, date) from the text using regex.
        Returns a dictionary of found details.
        """
        info = {}
        # Common fields and patterns in medical reports:
        match = re.search(r'Name\s*[:\-]\s*([A-Za-z .,\']+)', text, flags=re.IGNORECASE)
        if match:
            info['name'] = match.group(1).strip()
        match = re.search(r'Patient ID\s*[:\-]\s*([A-Za-z0-9\-]+)', text, flags=re.IGNORECASE)
        if match:
            info['id'] = match.group(1).strip()
        match = re.search(r'Age\s*[:\-]\s*([0-9]+)', text, flags=re.IGNORECASE)
        if match:
            try:
                info['age'] = int(match.group(1))
            except ValueError:
                info['age'] = match.group(1)
        match = re.search(r'\bSex\s*[:\-]\s*(Male|Female|Other)', text, flags=re.IGNORECASE)
        if match:
            info['gender'] = match.group(1).title()
        # Find a date in the text (report or visit date). Look for dd/mm/yyyy or similar.
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
        if date_match:
            date_str = date_match.group(1)
            # Try multiple date formats
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y-%m-%d"):
                try:
                    info['date'] = datetime.strptime(date_str, fmt)
                    break
                except Exception:
                    continue
        return info
    
    def extract_structured_data(self, pages_text: list, patient_id: str = None):
        """
        Convert the extracted text into structured data records.
        Returns a tuple: (patient_info_dict, records_list, full_text, pages_text_list).
        Each record is a dict with keys: patient_id, timestamp, metric_name, value, unit, source.
        """
        full_text = "\n".join(pages_text)
        patient_info = self.parse_patient_info(full_text)
        # Use provided patient_id if given (e.g., from context), otherwise from extracted info
        pid = patient_id or patient_info.get('id') or ""
        # Determine timestamp for records: use extracted date or current time if not found
        record_date = patient_info.get('date', None)
        if not record_date:
            record_date = datetime.now()
        records = []
        lines = full_text.splitlines()
        i = 0
        # Loop through lines to extract metrics and observations
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            # Skip lines that contain patient demographic info (already captured)
            low = line.lower()
            if any(key in low for key in ["patient name", "patient id", "name:", "age:", "sex:", "gender:", "date of birth", "dob"]):
                i += 1
                continue
            # Check for section headings that indicate clinical observations (Impression, Diagnosis, etc.)
            section_match = re.match(r'^(Impression|Diagnosis|Diagnoses|Conclusion|Assessment|Findings)[:\s]', line)
            if section_match:
                # Collect all lines in this section until an empty line or another section heading
                section_lines = []
                i += 1
                while i < len(lines):
                    nxt = lines[i].strip()
                    if not nxt:  # blank line denotes end of section
                        i += 1
                        break
                    # If a new section heading is encountered, stop (do not consume it)
                    if re.match(r'^[A-Z][A-Za-z ]+[:]', nxt):
                        break
                    section_lines.append(nxt)
                    i += 1
                # Parse collected section lines as diagnosis/impression findings
                records.extend(self._parse_diagnosis_section(section_lines, pid, record_date))
                continue  # continue outer loop (i is already at end of section or new heading)
            # Otherwise, try to parse the line as a test result or measurement
            rec = self._parse_test_line(line, pid, record_date)
            if rec:
                records.append(rec)
            i += 1
        return patient_info, records, full_text, pages_text
    
    def _parse_test_line(self, line: str, patient_id: str, timestamp: datetime):
        """
        Parse a single line for lab test results or measurements.
        Returns a record dict if the line contains a metric, otherwise None.
        """
        # Pattern 1: "TestName: value unit" or "TestName: Positive/Negative"
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            if not key or not val:
                return None
            # Ignore if the key is clearly a demographic or non-test field
            if key.lower() in ["name", "patient name", "patient id", "age", "sex", "gender", "dob"]:
                return None
            # If value is numeric with unit (e.g., "12.5 mg/dL")
            num_unit_match = re.match(r'^(-?\d+\.?\d*)\s*([A-Za-z/%]+)$', val)
            if num_unit_match:
                num_str = num_unit_match.group(1)
                unit = num_unit_match.group(2)
                try:
                    value = float(num_str) if ('.' in num_str) else int(num_str)
                except ValueError:
                    value = num_str  # if extremely large or special format, keep as string
                return {
                    "patient_id": patient_id, "timestamp": timestamp,
                    "metric_name": key, "value": value, "unit": unit, "source": "Document"
                }
            # If value is a standalone number (no unit)
            if re.match(r'^-?\d+\.?\d*$', val):
                try:
                    value = float(val) if '.' in val else int(val)
                except ValueError:
                    value = val
                return {
                    "patient_id": patient_id, "timestamp": timestamp,
                    "metric_name": key, "value": value, "unit": "", "source": "Document"
                }
            # If value is a textual result (e.g., "Positive", "Negative", "Normal")
            val_lower = val.lower()
            boolean_map = {"positive": True, "negative": False, "yes": True, "no": False, "present": True, "absent": False, "normal": "Normal", "abnormal": "Abnormal"}
            if val_lower in boolean_map:
                value = boolean_map[val_lower]
            else:
                value = val  # keep the text as value if it's descriptive
            return {
                "patient_id": patient_id, "timestamp": timestamp,
                "metric_name": key, "value": value, "unit": "", "source": "Document"
            }
        # Pattern 2: no colon, possibly tabular format "TestName    value [unit]"
        # e.g., "Glucose 100 mg/dL"
        match = re.match(r'^([A-Za-z0-9 \-/+()%]+)\s+(-?\d+\.?\d*(?:/\d+\.?\d*)?)\s*([A-Za-z/%]+)?', line)
        if match:
            name = match.group(1).strip().rstrip(":-")
            val_str = match.group(2)
            unit = match.group(3) if match.group(3) else ""
            # Attempt to convert value string to numeric, handle composite like "120/80"
            if '/' in val_str:
                # Composite values (e.g., blood pressure) stored as string
                value = val_str
            else:
                try:
                    value = float(val_str) if '.' in val_str else int(val_str)
                except ValueError:
                    value = val_str
            return {
                "patient_id": patient_id, "timestamp": timestamp,
                "metric_name": name, "value": value, "unit": unit, "source": "Document"
            }
        # Pattern 3: Text without colon indicating a qualitative result e.g., "TestName Negative"
        match = re.match(r'^([A-Za-z0-9 \-/()+%]+)\s+(Positive|Negative|positive|negative|Normal|Abnormal)$', line)
        if match:
            name = match.group(1).strip().rstrip(":-")
            result_word = match.group(2).lower()
            value = True if result_word in ["positive", "abnormal"] else False if result_word == "negative" else result_word.title()
            return {
                "patient_id": patient_id, "timestamp": timestamp,
                "metric_name": name, "value": value, "unit": "", "source": "Document"
            }
        return None
    
    def _parse_diagnosis_section(self, lines: list, patient_id: str, timestamp: datetime):
        """
        Parse lines from a diagnosis/impression/findings section to extract conditions or observations.
        Returns a list of record dicts for each identified health event.
        """
        records = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            # Remove list numbering or bullet characters from the start
            line = re.sub(r'^[0-9]+[\).]\s*', '', line)
            line = line.lstrip("-* \t")
            if not line:
                continue
            # If multiple conditions are listed in one line separated by ';' or ' and ', split them
            parts = re.split(r';| and |\.\s+', line)
            for part in parts:
                phrase = part.strip().rstrip(".")
                if not phrase:
                    continue
                # Determine value (presence/severity) and metric_name from phrase
                value = True  # default presence
                words = phrase.split()
                # Check for negation at start
                if words[0].lower() in ["no", "no.", "none", "no,"]:
                    value = False
                    words = words[1:]
                    phrase = " ".join(words)
                if not phrase:
                    continue
                # Check for severity descriptors at start (e.g., Mild/Moderate/Severe)
                severity_terms = {"mild", "moderate", "severe", "significant", "slight", "minor", "major"}
                if words[0].lower() in severity_terms:
                    # Handle cases like "Moderate to severe"
                    severity = words[0].capitalize()
                    if len(words) > 2 and words[1].lower() == "to" and words[2].lower() in severity_terms:
                        severity = f"{words[0].capitalize()} to {words[2].lower()}"
                        words = words[3:]
                    else:
                        words = words[1:]
                    if value not in (False, None):
                        # Use severity description as value if condition is present
                        value = severity
                    phrase = " ".join(words)
                # Remove trailing common words like "present/seen/noted" 
                phrase = re.sub(r'\b(present|seen|noted|identified)\b', '', phrase, flags=re.IGNORECASE).strip(",;: ")
                if not phrase:
                    continue
                metric_name = phrase[0].upper() + phrase[1:] if phrase else phrase
                records.append({
                    "patient_id": patient_id, 
                    "timestamp": timestamp,
                    "metric_name": metric_name,
                    "value": value,
                    "unit": "", 
                    "source": "Impression"
                })
        return records
