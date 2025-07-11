"""
Document Reader Agent for CrewAI pipeline.
Responsible for extracting and segmenting text from PDF documents.
"""

import json
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from io import BytesIO
from typing import Dict, Any, List
from datetime import datetime

from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.logging import logger


class DocumentSegments(BaseModel):
    """Model for document text segments."""
    patient_id: str = Field(default="Not Available", description="Patient identifier")
    document_title: str = Field(default="Not Available", description="Document title or type")
    document_date: str = Field(default="Not Available", description="Document date")
    full_text: str = Field(description="Complete extracted text")
    sections: Dict[str, str] = Field(default_factory=dict, description="Organized text sections")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PDFReaderTool(BaseTool):
    """Tool for reading PDF documents with OCR fallback."""
    
    name: str = "pdf_reader"
    description: str = "Extract text from PDF documents with OCR support for scanned documents"
    
    def _run(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF file."""
        try:
            logger.info(f"Reading PDF: {file_path}")
            
            # Open PDF
            doc = fitz.open(file_path)
            pages_text = []
            total_text = ""
            has_text = False
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Try text extraction first
                text = page.get_text()
                
                if text.strip():
                    has_text = True
                    pages_text.append({
                        "page": page_num + 1,
                        "text": text.strip(),
                        "method": "text_extraction"
                    })
                    total_text += f"\n--- Page {page_num + 1} ---\n{text}"
                else:
                    # Fallback to OCR for scanned pages
                    logger.info(f"No text found on page {page_num + 1}, using OCR")
                    
                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution
                    img_data = pix.tobytes("png")
                    img = Image.open(BytesIO(img_data))
                    
                    # Perform OCR
                    ocr_text = pytesseract.image_to_string(img, config='--psm 6')
                    
                    if ocr_text.strip():
                        pages_text.append({
                            "page": page_num + 1,
                            "text": ocr_text.strip(),
                            "method": "ocr"
                        })
                        total_text += f"\n--- Page {page_num + 1} (OCR) ---\n{ocr_text}"
            
            doc.close()
            
            # Parse sections if possible
            sections = self._parse_sections(total_text)
            
            # Extract basic metadata
            patient_id = self._extract_patient_id(total_text)
            document_date = self._extract_document_date(total_text)
            document_title = self._extract_document_title(total_text)
            
            return {
                "success": True,
                "patient_id": patient_id,
                "document_title": document_title,
                "document_date": document_date,
                "full_text": total_text.strip(),
                "sections": sections,
                "pages": pages_text,
                "metadata": {
                    "page_count": len(doc),
                    "has_native_text": has_text,
                    "extraction_method": "mixed" if not has_text else "native",
                    "extracted_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "full_text": "",
                "sections": {},
                "metadata": {}
            }
    
    def _parse_sections(self, text: str) -> Dict[str, str]:
        """Parse text into SOAP or other medical sections."""
        sections = {}
        
        # Common medical section headers
        section_patterns = {
            "subjective": ["subjective:", "s:", "chief complaint:", "history:", "patient reports:"],
            "objective": ["objective:", "o:", "physical exam:", "examination:", "vital signs:"],
            "assessment": ["assessment:", "a:", "diagnosis:", "impression:", "diagnoses:"],
            "plan": ["plan:", "p:", "treatment:", "recommendations:", "follow-up:"],
            "history": ["medical history:", "past medical history:", "pmh:", "hpi:"],
            "medications": ["medications:", "current medications:", "meds:", "prescriptions:"],
            "allergies": ["allergies:", "drug allergies:", "nkda:", "nka:"]
        }
        
        text_lower = text.lower()
        
        # Find section boundaries
        section_positions = []
        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                pos = text_lower.find(pattern)
                if pos != -1:
                    section_positions.append((pos, section_name, pattern))
        
        # Sort by position
        section_positions.sort()
        
        # Extract section content
        for i, (pos, section_name, pattern) in enumerate(section_positions):
            start_pos = pos + len(pattern)
            
            # Find end position (next section or end of text)
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
            else:
                end_pos = len(text)
            
            section_text = text[start_pos:end_pos].strip()
            if section_text:
                sections[section_name] = section_text
        
        # If no sections found, use full text
        if not sections:
            sections["full_text"] = text
        
        return sections
    
    def _extract_patient_id(self, text: str) -> str:
        """Extract patient identifier from text."""
        import re
        
        # Common patterns for patient IDs
        patterns = [
            r"patient\s*(?:id|#|number):\s*([A-Z0-9\-]+)",
            r"mrn:\s*([A-Z0-9\-]+)",
            r"medical\s*record\s*(?:number|#):\s*([A-Z0-9\-]+)",
            r"id:\s*([A-Z0-9\-]+)"
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1).upper()
        
        # Try to extract from patient name patterns
        name_patterns = [
            r"patient:\s*([A-Za-z\s,]+)",
            r"name:\s*([A-Za-z\s,]+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match:
                name = match.group(1).strip().title()
                if len(name) > 2 and len(name) < 50:  # Reasonable name length
                    return name
        
        return "Not Available"
    
    def _extract_document_date(self, text: str) -> str:
        """Extract document date from text."""
        import re
        
        # Date patterns
        patterns = [
            r"date:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{4}-\d{2}-\d{2})",
            r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}"
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1)
        
        return "Not Available"
    
    def _extract_document_title(self, text: str) -> str:
        """Extract document title or type."""
        # Look for common medical document types
        document_types = [
            "soap note", "progress note", "consultation", "discharge summary",
            "operative report", "pathology report", "radiology report",
            "emergency department", "clinic note", "therapy note",
            "injury report", "evaluation", "assessment"
        ]
        
        text_lower = text.lower()
        for doc_type in document_types:
            if doc_type in text_lower:
                return doc_type.title()
        
        # Extract from first line if it looks like a title
        first_lines = text.split('\n')[:3]
        for line in first_lines:
            if len(line.strip()) > 5 and len(line.strip()) < 100:
                if any(word in line.lower() for word in ["report", "note", "summary", "evaluation"]):
                    return line.strip()
        
        return "Medical Document"


class DocumentReaderAgent:
    """CrewAI agent for document reading and text extraction."""
    
    def __init__(self):
        self.pdf_tool = PDFReaderTool()
        
        self.agent = Agent(
            role="Medical Document Reader",
            goal="Extract and organize text content from medical PDF documents with high accuracy",
            backstory="""You are a specialized document processing expert with years of experience 
            in medical record digitization. You excel at extracting text from various document formats,
            including scanned PDFs, and organizing content into structured sections following medical 
            documentation standards like SOAP notes.""",
            tools=[self.pdf_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
    
    def create_extraction_task(self, file_path: str, document_id: str) -> Task:
        """Create a task for document text extraction."""
        
        return Task(
            description=f"""
            Extract all textual content from the medical PDF document at '{file_path}'.
            
            Your task is to:
            1. Read the PDF file using available tools
            2. Extract all text content, using OCR for scanned pages if needed
            3. Identify and organize text into logical sections (SOAP format if present)
            4. Extract basic metadata like patient ID, document date, and document type
            5. Preserve the complete text while organizing it for downstream processing
            
            Document ID: {document_id}
            
            Return the complete extracted content following this JSON structure:
            {{
                "patient_id": "extracted patient identifier or 'Not Available'",
                "document_title": "document type or title",
                "document_date": "document date if found",
                "full_text": "complete extracted text",
                "sections": {{
                    "subjective": "subjective section text",
                    "objective": "objective section text", 
                    "assessment": "assessment section text",
                    "plan": "plan section text"
                }},
                "metadata": {{
                    "page_count": number,
                    "extraction_method": "native|ocr|mixed",
                    "extracted_at": "ISO timestamp"
                }}
            }}
            
            Ensure NO text content is lost during extraction. If section headers are not found,
            include all text under 'full_text' and leave sections empty.
            """,
            expected_output="Complete JSON document with extracted text organized into sections",
            agent=self.agent
        )
    
    def extract_document_text(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """Extract text from document using the agent."""
        try:
            # Use the tool directly for now
            return self.pdf_tool._run(file_path)
        except Exception as e:
            logger.error(f"Document extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "full_text": "",
                "sections": {},
                "metadata": {}
            }
