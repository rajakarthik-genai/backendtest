"""
Medical Terminology Normalization Module

This module provides functionality to normalize medical terms using standard
medical vocabularies (SNOMED-CT, ICD-10/UMLS) for better data consistency
and semantic search capabilities.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MedicalTerm:
    """Represents a normalized medical term."""
    original_term: str
    normalized_term: str
    category: str
    confidence: float
    codes: Dict[str, str]  # e.g., {"icd10": "I10", "snomed": "38341003"}


class MedicalTerminologyMapper:
    """
    Maps medical terms to standardized vocabularies and handles synonyms.
    
    This is a simplified implementation. In production, you would integrate
    with proper medical terminology services like UMLS API.
    """
    
    def __init__(self):
        """Initialize the terminology mapper with common medical synonyms."""
        self.condition_synonyms = {
            # Cardiovascular
            "heart attack": "myocardial infarction",
            "mi": "myocardial infarction",
            "stroke": "cerebrovascular accident", 
            "cva": "cerebrovascular accident",
            "high blood pressure": "hypertension",
            "htn": "hypertension",
            "afib": "atrial fibrillation",
            "a-fib": "atrial fibrillation",
            
            # Respiratory
            "shortness of breath": "dyspnea",
            "sob": "dyspnea",
            "difficulty breathing": "dyspnea",
            "copd": "chronic obstructive pulmonary disease",
            "pneumonia": "pneumonia",
            "asthma": "asthma",
            
            # Diabetes
            "diabetes": "diabetes mellitus",
            "dm": "diabetes mellitus",
            "t1dm": "type 1 diabetes mellitus",
            "t2dm": "type 2 diabetes mellitus",
            "high blood sugar": "hyperglycemia",
            "low blood sugar": "hypoglycemia",
            
            # Musculoskeletal
            "arthritis": "arthritis",
            "osteoarthritis": "osteoarthritis",
            "oa": "osteoarthritis",
            "rheumatoid arthritis": "rheumatoid arthritis",
            "ra": "rheumatoid arthritis",
            "back pain": "dorsalgia",
            "lower back pain": "low back pain",
            
            # Gastrointestinal
            "gerd": "gastroesophageal reflux disease",
            "acid reflux": "gastroesophageal reflux disease",
            "heartburn": "gastroesophageal reflux disease",
            "ibs": "irritable bowel syndrome",
            "crohn's": "crohn's disease",
            "uc": "ulcerative colitis",
            
            # Neurological
            "seizure": "seizure disorder",
            "epilepsy": "epilepsy",
            "migraine": "migraine headache",
            "headache": "cephalgia",
            "parkinson's": "parkinson's disease",
            "alzheimer's": "alzheimer's disease",
            
            # Mental Health
            "depression": "major depressive disorder",
            "anxiety": "anxiety disorder",
            "ptsd": "post-traumatic stress disorder",
            "adhd": "attention deficit hyperactivity disorder",
            "ocd": "obsessive-compulsive disorder",
            
            # Cancer
            "cancer": "malignant neoplasm",
            "tumor": "neoplasm",
            "mass": "space-occupying lesion",
            "lymphoma": "lymphoma",
            "leukemia": "leukemia",
            
            # Other
            "kidney disease": "chronic kidney disease",
            "ckd": "chronic kidney disease",
            "liver disease": "hepatic disorder",
            "thyroid problems": "thyroid disorder",
            "anemia": "anemia"
        }
        
        self.body_part_synonyms = {
            # Anatomical synonyms
            "stomach": "abdomen",
            "belly": "abdomen", 
            "tummy": "abdomen",
            "chest": "thorax",
            "back": "spine",
            "backbone": "spine",
            "hip": "pelvis",
            "knee joint": "knee",
            "elbow joint": "elbow",
            "shoulder joint": "shoulder",
            "wrist": "hand",
            "ankle": "foot",
            "calf": "leg",
            "thigh": "leg",
            "forearm": "arm",
            "upper arm": "arm"
        }
        
        # Simplified ICD-10 codes (subset for demonstration)
        self.icd10_codes = {
            "hypertension": "I10",
            "myocardial infarction": "I21.9",
            "diabetes mellitus": "E11.9",
            "asthma": "J45.9",
            "pneumonia": "J18.9",
            "chronic obstructive pulmonary disease": "J44.1",
            "osteoarthritis": "M19.9",
            "major depressive disorder": "F32.9",
            "anxiety disorder": "F41.9",
            "chronic kidney disease": "N18.9"
        }
        
        # Simplified SNOMED-CT codes (subset for demonstration)
        self.snomed_codes = {
            "hypertension": "38341003",
            "myocardial infarction": "22298006", 
            "diabetes mellitus": "73211009",
            "asthma": "195967001",
            "pneumonia": "233604007",
            "chronic obstructive pulmonary disease": "13645005",
            "osteoarthritis": "396275006",
            "major depressive disorder": "370143000",
            "anxiety disorder": "197480006",
            "chronic kidney disease": "709044004"
        }
    
    def normalize_condition(self, condition: str) -> MedicalTerm:
        """
        Normalize a medical condition to standard terminology.
        
        Args:
            condition: Raw medical condition text
            
        Returns:
            MedicalTerm with normalized information
        """
        if not condition:
            return None
        
        # Clean and lowercase
        cleaned = self._clean_text(condition)
        
        # Check for direct synonym match
        normalized = self.condition_synonyms.get(cleaned, cleaned)
        
        # Look for partial matches if no direct match
        if normalized == cleaned:
            normalized = self._find_partial_match(cleaned, self.condition_synonyms)
        
        # Get medical codes
        codes = {}
        if normalized in self.icd10_codes:
            codes["icd10"] = self.icd10_codes[normalized]
        if normalized in self.snomed_codes:
            codes["snomed"] = self.snomed_codes[normalized]
        
        # Calculate confidence based on match quality
        confidence = 1.0 if cleaned in self.condition_synonyms else 0.8
        if not codes:
            confidence *= 0.7  # Lower confidence if no standard codes found
        
        return MedicalTerm(
            original_term=condition,
            normalized_term=normalized,
            category="condition",
            confidence=confidence,
            codes=codes
        )
    
    def normalize_body_part(self, body_part: str) -> Optional[str]:
        """
        Normalize body part terminology.
        
        Args:
            body_part: Raw body part text
            
        Returns:
            Normalized body part name
        """
        if not body_part:
            return None
        
        cleaned = self._clean_text(body_part)
        
        # Check for synonym match
        normalized = self.body_part_synonyms.get(cleaned, cleaned)
        
        # Look for partial matches
        if normalized == cleaned:
            normalized = self._find_partial_match(cleaned, self.body_part_synonyms)
        
        return normalized
    
    def extract_medical_abbreviations(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract and expand medical abbreviations from text.
        
        Args:
            text: Medical text
            
        Returns:
            List of (abbreviation, expansion) tuples
        """
        if not text:
            return []
        
        abbreviations = []
        text_lower = text.lower()
        
        # Common medical abbreviations
        med_abbreviations = {
            "bp": "blood pressure",
            "hr": "heart rate",
            "rr": "respiratory rate",
            "temp": "temperature",
            "wt": "weight",
            "ht": "height",
            "bmi": "body mass index",
            "ecg": "electrocardiogram",
            "ekg": "electrocardiogram",
            "cxr": "chest x-ray",
            "ct": "computed tomography",
            "mri": "magnetic resonance imaging",
            "lab": "laboratory",
            "cbc": "complete blood count",
            "bmp": "basic metabolic panel",
            "lfts": "liver function tests",
            "ua": "urinalysis",
            "pt": "patient",
            "hx": "history",
            "sx": "symptoms",
            "tx": "treatment",
            "dx": "diagnosis",
            "rx": "prescription",
            "f/u": "follow up",
            "wnl": "within normal limits",
            "nkda": "no known drug allergies",
            "nkfa": "no known food allergies"
        }
        
        # Find abbreviations in text
        for abbrev, expansion in med_abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, text_lower):
                abbreviations.append((abbrev.upper(), expansion))
        
        return abbreviations
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for matching."""
        if not text:
            return ""
        
        # Convert to lowercase
        cleaned = text.lower().strip()
        
        # Remove common prefixes/suffixes
        cleaned = re.sub(r'^(acute|chronic|severe|mild|moderate)\s+', '', cleaned)
        cleaned = re.sub(r'\s+(disorder|disease|syndrome|condition)$', '', cleaned)
        
        # Remove punctuation and extra spaces
        cleaned = re.sub(r'[^\w\s-]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _find_partial_match(self, term: str, dictionary: Dict[str, str]) -> str:
        """Find partial matches in dictionary."""
        # Look for substring matches
        for key, value in dictionary.items():
            if term in key or key in term:
                return value
        
        # Look for word matches
        term_words = set(term.split())
        for key, value in dictionary.items():
            key_words = set(key.split())
            if term_words & key_words:  # Intersection
                return value
        
        return term  # Return original if no match found


# Global instance for easy import
medical_mapper = MedicalTerminologyMapper()


def normalize_medical_condition(condition: str) -> MedicalTerm:
    """Convenience function to normalize a medical condition."""
    return medical_mapper.normalize_condition(condition)


def normalize_body_part(body_part: str) -> Optional[str]:
    """Convenience function to normalize a body part."""
    return medical_mapper.normalize_body_part(body_part)


def expand_medical_abbreviations(text: str) -> List[Tuple[str, str]]:
    """Convenience function to extract medical abbreviations."""
    return medical_mapper.extract_medical_abbreviations(text)
