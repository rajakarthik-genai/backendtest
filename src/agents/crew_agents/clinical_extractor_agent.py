"""
Clinical Data Extractor Agent for CrewAI pipeline.
Specialized in extracting comprehensive medical information from clinical text.
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.logging import logger
from src.config.body_parts import get_default_body_parts


class MedicalEvent(BaseModel):
    """Model for medical events/findings."""
    description: str = Field(description="Description of the medical event")
    body_part: str = Field(description="Affected body part")
    date: str = Field(default="Not Available", description="Date of event")
    severity: str = Field(default="moderate", description="Severity level")
    source: Dict[str, Any] = Field(default_factory=dict, description="Source location in document")


class Diagnosis(BaseModel):
    """Model for medical diagnoses."""
    name: str = Field(description="Diagnosis name")
    code: str = Field(default="Not Available", description="Medical code (ICD-10/ICD-9)")
    date_diagnosed: str = Field(default="Not Available", description="Date of diagnosis")
    status: str = Field(default="active", description="Diagnosis status")
    source: Dict[str, Any] = Field(default_factory=dict, description="Source location in document")


class Procedure(BaseModel):
    """Model for medical procedures."""
    name: str = Field(description="Procedure name")
    date: str = Field(default="Not Available", description="Date performed")
    outcome: str = Field(default="Not Available", description="Procedure outcome")
    source: Dict[str, Any] = Field(default_factory=dict, description="Source location in document")


class Medication(BaseModel):
    """Model for medications."""
    name: str = Field(description="Medication name")
    dosage: str = Field(default="Not Available", description="Dosage")
    frequency: str = Field(default="Not Available", description="Frequency")
    source: Dict[str, Any] = Field(default_factory=dict, description="Source location in document")


class TimelineEvent(BaseModel):
    """Model for timeline events."""
    date: str = Field(description="Event date")
    event: str = Field(description="Event description")
    source_ref: Dict[str, Any] = Field(default_factory=dict, description="Source reference")


class ClinicalData(BaseModel):
    """Complete clinical data extraction model."""
    patient_id: str = Field(default="Not Available")
    patient_name: str = Field(default="Not Available")
    document_title: str = Field(default="Not Available")
    document_date: str = Field(default="Not Available")
    clinician: Dict[str, str] = Field(default_factory=dict)
    injuries: List[MedicalEvent] = Field(default_factory=list)
    diagnoses: List[Diagnosis] = Field(default_factory=list)
    procedures: List[Procedure] = Field(default_factory=list)
    medications: List[Medication] = Field(default_factory=list)
    subjective_note_text: str = Field(default="Not Available")
    objective_note_text: str = Field(default="Not Available")
    assessment_note_text: str = Field(default="Not Available")
    plan_note_text: str = Field(default="Not Available")
    feedback: str = Field(default="Not Available")
    recovery_progress: str = Field(default="Not Available")
    patient_history: str = Field(default="Not Available")
    timeline: List[TimelineEvent] = Field(default_factory=list)
    medical_codes: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MedicalExtractionTool(BaseTool):
    """Tool for extracting medical information from clinical text."""
    
    name: str = "medical_extractor"
    description: str = "Extract comprehensive medical information from clinical documents"
    
    def _run(self, text_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract medical information from text."""
        try:
            logger.info("Starting medical information extraction")
            
            full_text = text_data.get("full_text", "")
            sections = text_data.get("sections", {})
            
            if not full_text:
                return {"success": False, "error": "No text provided for extraction"}
            
            # Initialize extraction result
            clinical_data = {
                "patient_id": text_data.get("patient_id", "Not Available"),
                "patient_name": self._extract_patient_name(full_text),
                "document_title": text_data.get("document_title", "Not Available"),
                "document_date": text_data.get("document_date", "Not Available"),
                "clinician": self._extract_clinician_info(full_text),
                "injuries": self._extract_injuries(full_text),
                "diagnoses": self._extract_diagnoses(full_text),
                "procedures": self._extract_procedures(full_text),
                "medications": self._extract_medications(full_text),
                "subjective_note_text": sections.get("subjective", "Not Available"),
                "objective_note_text": sections.get("objective", "Not Available"),
                "assessment_note_text": sections.get("assessment", "Not Available"),
                "plan_note_text": sections.get("plan", "Not Available"),
                "feedback": self._extract_feedback(full_text),
                "recovery_progress": self._extract_recovery_progress(full_text),
                "patient_history": self._extract_patient_history(full_text, sections),
                "timeline": self._extract_timeline(full_text),
                "medical_codes": self._extract_medical_codes(full_text),
                "metadata": {
                    "extraction_date": datetime.utcnow().isoformat(),
                    "source_file": text_data.get("metadata", {}).get("source_file", "Unknown"),
                    "page_count": text_data.get("metadata", {}).get("page_count", 1),
                    "extraction_method": "comprehensive_nlp"
                }
            }
            
            return {
                "success": True,
                "clinical_data": clinical_data
            }
            
        except Exception as e:
            logger.error(f"Medical extraction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_patient_name(self, text: str) -> str:
        """Extract patient name from text."""
        patterns = [
            r"patient\s*(?:name)?:\s*([A-Za-z\s,\.]+)",
            r"name:\s*([A-Za-z\s,\.]+)",
            r"pt\s*(?:name)?:\s*([A-Za-z\s,\.]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up name
                name = re.sub(r'[,\.]', '', name).strip()
                if 2 < len(name) < 50 and not any(char.isdigit() for char in name):
                    return name.title()
        
        return "Not Available"
    
    def _extract_clinician_info(self, text: str) -> Dict[str, str]:
        """Extract clinician information."""
        clinician_info = {
            "name": "Not Available",
            "role": "Not Available",
            "provider_id": "Not Available"
        }
        
        # Patterns for clinician names and roles
        patterns = [
            r"(?:dr\.?|doctor|physician|therapist|provider)\s*:?\s*([A-Za-z\s,\.]+)",
            r"(?:signed|reviewed|authored)\s*by\s*:?\s*([A-Za-z\s,\.]+)",
            r"([A-Za-z\s,\.]+),?\s*(?:md|do|pt|np|pa)",
            r"clinician\s*:?\s*([A-Za-z\s,\.]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = re.sub(r'[,\.]', '', name).strip()
                if 2 < len(name) < 50:
                    clinician_info["name"] = name.title()
                    break
        
        # Extract role
        role_patterns = [
            r"(physical\s*therapist|pt)",
            r"(physician|doctor|md|do)",
            r"(nurse\s*practitioner|np)",
            r"(physician\s*assistant|pa)",
            r"(therapist)",
            r"(specialist)"
        ]
        
        for pattern in role_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                clinician_info["role"] = pattern.replace("\\s*", " ").replace("(", "").replace(")", "").title()
                break
        
        return clinician_info
    
    def _extract_injuries(self, text: str) -> List[Dict[str, Any]]:
        """Extract injury information."""
        injuries = []
        body_parts = get_default_body_parts()
        
        # Injury-related keywords
        injury_keywords = [
            "strain", "sprain", "tear", "fracture", "injury", "trauma",
            "pain", "swelling", "inflammation", "bruise", "contusion",
            "dislocation", "subluxation", "laceration", "abrasion"
        ]
        
        # Look for injury descriptions
        for body_part in body_parts:
            for keyword in injury_keywords:
                pattern = rf"({body_part.lower()})\s*.*?({keyword})"
                matches = re.finditer(pattern, text.lower())
                
                for match in matches:
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(text), match.end() + 100)
                    context = text[start_pos:end_pos].strip()
                    
                    # Extract severity
                    severity = "moderate"
                    if any(word in context.lower() for word in ["severe", "critical", "major"]):
                        severity = "severe"
                    elif any(word in context.lower() for word in ["mild", "minor", "slight"]):
                        severity = "mild"
                    
                    # Extract date
                    date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', context)
                    event_date = date_match.group(0) if date_match else "Not Available"
                    
                    injury = {
                        "description": context,
                        "body_part": body_part,
                        "date": event_date,
                        "severity": severity,
                        "source": {
                            "offset": [match.start(), match.end()],
                            "context": context
                        }
                    }
                    
                    injuries.append(injury)
        
        # Remove duplicates based on description similarity
        unique_injuries = []
        for injury in injuries:
            is_duplicate = False
            for existing in unique_injuries:
                if (injury["body_part"] == existing["body_part"] and 
                    injury["severity"] == existing["severity"]):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_injuries.append(injury)
        
        return unique_injuries[:10]  # Limit to avoid excessive results
    
    def _extract_diagnoses(self, text: str) -> List[Dict[str, Any]]:
        """Extract diagnosis information."""
        diagnoses = []
        
        # Common diagnosis patterns
        diagnosis_patterns = [
            r"diagnosis\s*:?\s*([^\n\r]+)",
            r"impression\s*:?\s*([^\n\r]+)",
            r"assessment\s*:?\s*([^\n\r]+)",
            r"icd[^\s]*\s*:?\s*([^\n\r]+)"
        ]
        
        for pattern in diagnosis_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                diagnosis_text = match.group(1).strip()
                
                # Extract ICD codes
                icd_match = re.search(r'(\d{3}\.?\d*)', diagnosis_text)
                code = icd_match.group(0) if icd_match else "Not Available"
                
                # Clean diagnosis name
                clean_diagnosis = re.sub(r'\d{3}\.?\d*', '', diagnosis_text).strip()
                clean_diagnosis = re.sub(r'[^\w\s]', ' ', clean_diagnosis).strip()
                
                if clean_diagnosis and len(clean_diagnosis) > 3:
                    diagnosis = {
                        "name": clean_diagnosis,
                        "code": code,
                        "date_diagnosed": "Not Available",
                        "status": "active",
                        "source": {
                            "offset": [match.start(), match.end()],
                            "context": match.group(0)
                        }
                    }
                    diagnoses.append(diagnosis)
        
        return diagnoses[:5]  # Limit results
    
    def _extract_procedures(self, text: str) -> List[Dict[str, Any]]:
        """Extract procedure information."""
        procedures = []
        
        procedure_keywords = [
            "surgery", "procedure", "treatment", "therapy", "injection",
            "examination", "test", "scan", "x-ray", "mri", "ct", "ultrasound"
        ]
        
        for keyword in procedure_keywords:
            pattern = rf"({keyword})\s*:?\s*([^\n\r]+)"
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                procedure_text = match.group(2).strip()
                
                # Extract date
                date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', procedure_text)
                proc_date = date_match.group(0) if date_match else "Not Available"
                
                procedure = {
                    "name": f"{keyword.title()}: {procedure_text}",
                    "date": proc_date,
                    "outcome": "Not Available",
                    "source": {
                        "offset": [match.start(), match.end()],
                        "context": match.group(0)
                    }
                }
                procedures.append(procedure)
        
        return procedures[:5]  # Limit results
    
    def _extract_medications(self, text: str) -> List[Dict[str, Any]]:
        """Extract medication information."""
        medications = []
        
        # Medication section patterns
        med_patterns = [
            r"medications?\s*:?\s*([^\n\r]+)",
            r"prescriptions?\s*:?\s*([^\n\r]+)",
            r"drugs?\s*:?\s*([^\n\r]+)"
        ]
        
        for pattern in med_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                med_text = match.group(1).strip()
                
                # Split multiple medications
                med_list = re.split(r'[,;]', med_text)
                
                for med in med_list:
                    med = med.strip()
                    if len(med) > 2:
                        # Extract dosage
                        dosage_match = re.search(r'(\d+\s*mg|\d+\s*ml|\d+\s*units?)', med, re.IGNORECASE)
                        dosage = dosage_match.group(0) if dosage_match else "Not Available"
                        
                        # Extract frequency
                        freq_patterns = [
                            r'(daily|bid|tid|qid|q\d+h|once|twice|three times)',
                            r'(\d+\s*times?\s*(?:per\s*)?day)',
                            r'(every\s*\d+\s*hours?)'
                        ]
                        
                        frequency = "Not Available"
                        for freq_pattern in freq_patterns:
                            freq_match = re.search(freq_pattern, med, re.IGNORECASE)
                            if freq_match:
                                frequency = freq_match.group(0)
                                break
                        
                        medication = {
                            "name": med,
                            "dosage": dosage,
                            "frequency": frequency,
                            "source": {
                                "offset": [match.start(), match.end()],
                                "context": match.group(0)
                            }
                        }
                        medications.append(medication)
        
        return medications[:10]  # Limit results
    
    def _extract_feedback(self, text: str) -> str:
        """Extract patient or clinician feedback."""
        feedback_patterns = [
            r"feedback\s*:?\s*([^\n\r]+)",
            r"patient\s*(?:reports?|states?|says?)\s*:?\s*([^\n\r]+)",
            r"notes?\s*:?\s*([^\n\r]+)",
            r"comments?\s*:?\s*([^\n\r]+)"
        ]
        
        feedback_sections = []
        for pattern in feedback_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                feedback_text = match.group(1).strip()
                if len(feedback_text) > 10:
                    feedback_sections.append(feedback_text)
        
        return " | ".join(feedback_sections) if feedback_sections else "Not Available"
    
    def _extract_recovery_progress(self, text: str) -> str:
        """Extract recovery progress information."""
        progress_keywords = [
            "improvement", "progress", "recovery", "healing", "better",
            "worse", "unchanged", "stable", "deteriorating", "responding"
        ]
        
        progress_info = []
        for keyword in progress_keywords:
            pattern = rf"({keyword})\s*:?\s*([^\n\r]+)"
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context = match.group(0).strip()
                if len(context) > 10:
                    progress_info.append(context)
        
        return " | ".join(progress_info[:3]) if progress_info else "Not Available"
    
    def _extract_patient_history(self, text: str, sections: Dict[str, str]) -> str:
        """Extract patient medical history."""
        history_patterns = [
            r"(?:past\s*)?medical\s*history\s*:?\s*([^\n\r]+)",
            r"pmh\s*:?\s*([^\n\r]+)",
            r"history\s*:?\s*([^\n\r]+)",
            r"background\s*:?\s*([^\n\r]+)"
        ]
        
        history_sections = []
        
        # Check if there's a dedicated history section
        if "history" in sections:
            history_sections.append(sections["history"])
        
        # Extract from patterns
        for pattern in history_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                history_text = match.group(1).strip()
                if len(history_text) > 10:
                    history_sections.append(history_text)
        
        return " | ".join(history_sections) if history_sections else "Not Available"
    
    def _extract_timeline(self, text: str) -> List[Dict[str, Any]]:
        """Extract chronological timeline of events."""
        timeline = []
        
        # Find date references with associated events
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        date_matches = re.finditer(date_pattern, text)
        
        for match in date_matches:
            date_str = match.group(0)
            start_pos = max(0, match.start() - 100)
            end_pos = min(len(text), match.end() + 200)
            context = text[start_pos:end_pos].strip()
            
            # Extract event description around the date
            sentences = re.split(r'[.!?]', context)
            event_sentence = ""
            for sentence in sentences:
                if date_str in sentence:
                    event_sentence = sentence.strip()
                    break
            
            if event_sentence and len(event_sentence) > 10:
                timeline_event = {
                    "date": date_str,
                    "event": event_sentence,
                    "source_ref": {
                        "offset": [match.start(), match.end()],
                        "context": context
                    }
                }
                timeline.append(timeline_event)
        
        # Sort by date (basic sorting)
        return sorted(timeline, key=lambda x: x["date"])[:10]  # Limit results
    
    def _extract_medical_codes(self, text: str) -> List[Dict[str, str]]:
        """Extract medical codes (ICD, CPT, etc.)."""
        codes = []
        
        # ICD codes
        icd_pattern = r'(icd[^\s]*)\s*:?\s*(\d{3}\.?\d*)'
        icd_matches = re.finditer(icd_pattern, text, re.IGNORECASE)
        for match in icd_matches:
            codes.append({
                "code": match.group(2),
                "description": f"ICD Code: {match.group(2)}",
                "source": {
                    "offset": [match.start(), match.end()],
                    "context": match.group(0)
                }
            })
        
        # CPT codes
        cpt_pattern = r'(cpt)\s*:?\s*(\d{5})'
        cpt_matches = re.finditer(cpt_pattern, text, re.IGNORECASE)
        for match in cpt_matches:
            codes.append({
                "code": match.group(2),
                "description": f"CPT Code: {match.group(2)}",
                "source": {
                    "offset": [match.start(), match.end()],
                    "context": match.group(0)
                }
            })
        
        return codes


class ClinicalExtractorAgent:
    """CrewAI agent for comprehensive clinical data extraction."""
    
    def __init__(self):
        self.extraction_tool = MedicalExtractionTool()
        
        # Get available body parts for context
        body_parts = get_default_body_parts()
        body_parts_str = ", ".join(body_parts)
        
        self.agent = Agent(
            role="Clinical Information Extraction Specialist",
            goal="Extract comprehensive medical information from clinical documents with maximum accuracy and completeness",
            backstory=f"""You are a highly experienced medical information specialist with expertise 
            in clinical documentation, medical coding, and healthcare data extraction. You have worked 
            with thousands of medical records and understand the nuances of clinical language, SOAP notes, 
            medical terminology, and standardized medical codes.
            
            Available body parts for classification: {body_parts_str}
            
            Your expertise includes:
            - SOAP note interpretation and section identification
            - Medical terminology and clinical language processing
            - ICD-10/ICD-9 and CPT code recognition
            - Patient timeline construction from clinical narratives
            - Injury and diagnosis classification
            - Treatment and medication extraction
            - Clinical outcome assessment""",
            tools=[self.extraction_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def create_extraction_task(self, text_data: Dict[str, Any], document_id: str) -> Task:
        """Create a task for comprehensive medical data extraction."""
        
        return Task(
            description=f"""
            Perform comprehensive medical information extraction from the provided clinical text data.
            
            Input Data: {json.dumps(text_data, indent=2)}
            Document ID: {document_id}
            
            Your task is to extract ALL medically relevant information including:
            
            1. **Patient Information**: Patient ID, name, demographics
            2. **Clinician Information**: Name, role, provider ID if available
            3. **Injuries/Medical Events**: Description, affected body part, date, severity
            4. **Diagnoses**: Names, medical codes, dates, status (active/resolved)
            5. **Procedures**: Names, dates, outcomes
            6. **Medications**: Names, dosages, frequencies
            7. **Clinical Note Sections**: Full text of Subjective, Objective, Assessment, Plan sections
            8. **Patient Feedback**: Any patient-reported information or comments
            9. **Recovery Progress**: Progress notes, improvement status
            10. **Medical History**: Past medical history, background conditions
            11. **Timeline**: Chronological sequence of medical events with dates
            12. **Medical Codes**: ICD, CPT, or other standardized codes
            
            **Critical Requirements:**
            - Extract EVERY piece of medical information - do not omit anything
            - For each extracted item, include source provenance (text location/offset)
            - Use "Not Available" for missing information rather than omitting fields
            - Classify body parts using the provided standard list
            - Preserve complete section texts for embedding purposes
            - Extract dates in consistent format when available
            - Identify severity levels (mild/moderate/severe/critical) from context
            
            **Output Format:** Return a complete JSON object following the ClinicalData schema
            with all fields populated. Include provenance metadata for traceability.
            
            Be exhaustive and precise - this data will be used for patient care decisions.
            """,
            expected_output="Complete ClinicalData JSON object with comprehensive medical information extraction",
            agent=self.agent
        )
    
    def extract_clinical_data(self, text_data: Dict[str, Any], document_id: str) -> Dict[str, Any]:
        """Extract clinical data using the agent."""
        try:
            # Use the tool directly
            return self.extraction_tool._run(text_data)
        except Exception as e:
            logger.error(f"Clinical extraction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
