"""
Body part configurations for the MediTwin system.
This module defines the complete list of body parts for 3D visualization
and modular health tracking.
"""

from typing import List, Dict, Any

# Complete list of body parts for 3D model mapping
DEFAULT_BODY_PARTS = [
    # Head and Neck (10 parts)
    "Head",
    "Brain", 
    "Left Eye",
    "Right Eye",
    "Left Ear",
    "Right Ear",
    "Nose",
    "Mouth",
    "Neck",
    
    # Torso (10 parts)
    "Heart",
    "Left Lung",
    "Right Lung",
    "Liver",
    "Stomach",
    "Pancreas",
    "Spleen",
    "Left Kidney",
    "Right Kidney",
    "Spine",
    
    # Upper Body (6 parts)
    "Left Shoulder",
    "Right Shoulder",
    "Left Arm",
    "Right Arm",
    "Left Hand",
    "Right Hand",
    
    # Lower Body (10 parts)
    "Pelvis",
    "Left Hip",
    "Right Hip",
    "Left Leg",
    "Right Leg",
    "Left Knee",
    "Right Knee",
    "Left Foot",
    "Right Foot",
    
    # General (2 parts)
    "Left Ankle",
    "Right Ankle",
    "Skin"
]

# Ensure we have the expected count of body parts
assert len(DEFAULT_BODY_PARTS) == 37, f"Expected 37 body parts, got {len(DEFAULT_BODY_PARTS)}"

# Severity levels for body parts
SEVERITY_LEVELS = {
    "NA": "No data available",
    "normal": "Normal condition",
    "mild": "Mild issues detected",
    "moderate": "Moderate issues requiring attention",
    "severe": "Severe issues requiring immediate attention",
    "critical": "Critical condition"
}

# Mapping keywords to body parts for text extraction
BODY_PART_KEYWORDS = {
    # Head and Neck
    "head": "Head",
    "skull": "Head",
    "cranium": "Head",
    "brain": "Brain",
    "cerebral": "Brain",
    "neurological": "Brain",
    "left eye": "Left Eye",
    "right eye": "Right Eye",
    "eye": "Left Eye",  # Default to left, will be handled by laterality detection
    "ocular": "Left Eye",
    "vision": "Left Eye",
    "left ear": "Left Ear",
    "right ear": "Right Ear",
    "ear": "Left Ear",
    "hearing": "Left Ear",
    "nose": "Nose",
    "nasal": "Nose",
    "mouth": "Mouth",
    "oral": "Mouth",
    "dental": "Mouth",
    "throat": "Mouth",
    "neck": "Neck",
    "cervical": "Neck",
    
    # Torso
    "heart": "Heart",
    "cardiac": "Heart",
    "cardiovascular": "Heart",
    "left lung": "Left Lung",
    "right lung": "Right Lung",
    "lung": "Left Lung",
    "pulmonary": "Left Lung",
    "respiratory": "Left Lung",
    "liver": "Liver",
    "hepatic": "Liver",
    "stomach": "Stomach",
    "gastric": "Stomach",
    "pancreas": "Pancreas",
    "pancreatic": "Pancreas",
    "spleen": "Spleen",
    "splenic": "Spleen",
    "left kidney": "Left Kidney",
    "right kidney": "Right Kidney",
    "kidney": "Left Kidney",
    "renal": "Left Kidney",
    "spine": "Spine",
    "spinal": "Spine",
    "back": "Spine",
    "vertebral": "Spine",
    
    # Upper Body
    "left shoulder": "Left Shoulder",
    "right shoulder": "Right Shoulder",
    "shoulder": "Left Shoulder",
    "left arm": "Left Arm",
    "right arm": "Right Arm",
    "arm": "Left Arm",
    "left hand": "Left Hand",
    "right hand": "Right Hand",
    "hand": "Left Hand",
    
    # Lower Body
    "pelvis": "Pelvis",
    "pelvic": "Pelvis",
    "left hip": "Left Hip",
    "right hip": "Right Hip",
    "hip": "Left Hip",
    "left leg": "Left Leg",
    "right leg": "Right Leg",
    "leg": "Left Leg",
    "left knee": "Left Knee",
    "right knee": "Right Knee",
    "knee": "Left Knee",
    "left foot": "Left Foot",
    "right foot": "Right Foot",
    "foot": "Left Foot",
    "left ankle": "Left Ankle",
    "right ankle": "Right Ankle",
    "ankle": "Left Ankle",
    
    # General
    "skin": "Skin",
    "dermal": "Skin",
    "dermatological": "Skin"
}

def identify_body_parts_from_text(text: str) -> List[str]:
    """
    Extract body parts from text using keyword matching.
    Enhanced version with laterality detection.
    """
    if not text:
        return []
    
    text_lower = text.lower()
    body_parts = set()
    
    # Check for specific left/right mentions first
    for keyword, body_part in BODY_PART_KEYWORDS.items():
        if keyword in text_lower:
            # Handle laterality
            if "right" in text_lower and keyword in text_lower:
                if "left" not in body_part:  # Don't override already specific parts
                    body_parts.add(f"Right {body_part.replace('Left ', '')}")
                else:
                    body_parts.add(body_part.replace('Left ', 'Right '))
            elif "left" in text_lower and keyword in text_lower:
                if "right" not in body_part:
                    body_parts.add(f"Left {body_part.replace('Right ', '')}")
                else:
                    body_parts.add(body_part.replace('Right ', 'Left '))
            else:
                body_parts.add(body_part)
    
    return list(body_parts)


def get_default_body_parts() -> List[str]:
    """Get the default list of body parts."""
    return DEFAULT_BODY_PARTS.copy()


def get_severity_levels() -> Dict[str, str]:
    """Get the available severity levels."""
    return SEVERITY_LEVELS.copy()


def validate_body_part(body_part: str) -> bool:
    """Validate if a body part is in the default list."""
    return body_part in DEFAULT_BODY_PARTS


def add_body_part(body_part: str) -> bool:
    """
    Add a new body part to the system.
    This is for future modularity.
    """
    if body_part not in DEFAULT_BODY_PARTS:
        DEFAULT_BODY_PARTS.append(body_part)
        return True
    return False


def remove_body_part(body_part: str) -> bool:
    """
    Remove a body part from the system.
    This is for future modularity.
    """
    if body_part in DEFAULT_BODY_PARTS:
        DEFAULT_BODY_PARTS.remove(body_part)
        return True
    return False


# Create a dictionary mapping each body part to its basic configuration
BODY_PARTS = {
    body_part: {
        "name": body_part,
        "severity": "normal",  # Default severity
        "last_updated": None,
        "notes": ""
    }
    for body_part in DEFAULT_BODY_PARTS
}
