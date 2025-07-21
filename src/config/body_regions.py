# Regional body part configuration for MediTwin Agents
"""
Defines anatomical regions grouping the 30 body parts for regional analysis.
"""

# Regional mapping of body parts
BODY_REGIONS = {
    "head": [
        "Head",
        "Brain"
    ],
    "neck": [
        "Neck"
    ],
    "torso": [
        "Chest", 
        "Heart",
        "Lungs",
        "Abdomen",
        "Liver",
        "Kidneys",
        "Lower Back"
    ],
    "left_arm": [
        "Left Shoulder",
        "Left Arm", 
        "Left Elbow",
        "Left Wrist",
        "Left Hand"
    ],
    "right_arm": [
        "Right Shoulder",
        "Right Arm",
        "Right Elbow", 
        "Right Wrist",
        "Right Hand"
    ],
    "pelvis": [
        "Pelvis",
        "Hips"
    ],
    "left_leg": [
        "Left Hip",
        "Left Thigh",
        "Left Knee", 
        "Left Calf",
        "Left Ankle",
        "Left Foot"
    ],
    "right_leg": [
        "Right Hip",
        "Right Thigh",
        "Right Knee",
        "Right Calf", 
        "Right Ankle",
        "Right Foot"
    ]
}

def get_regions():
    """Get all available regions."""
    return list(BODY_REGIONS.keys())

def get_body_parts_for_region(region: str):
    """Get body parts that belong to a specific region."""
    return BODY_REGIONS.get(region, [])

def validate_region(region: str) -> bool:
    """Check if region is valid."""
    return region in BODY_REGIONS

def get_region_for_body_part(body_part: str):
    """Find which region a body part belongs to."""
    for region, parts in BODY_REGIONS.items():
        if body_part in parts:
            return region
    return None

# Severity hierarchy for regional aggregation
SEVERITY_HIERARCHY = {
    "NA": 0,
    "normal": 1,
    "mild": 2,
    "moderate": 3, 
    "severe": 4,
    "critical": 5
}

def aggregate_severities(severities: list) -> str:
    """
    Aggregate multiple severities to a single worst-case severity.
    
    Args:
        severities: List of severity strings
    
    Returns:
        Worst severity level
    """
    if not severities:
        return "NA"
    
    # Get the highest severity level
    max_severity = max(
        SEVERITY_HIERARCHY.get(s, 0) for s in severities
    )
    
    # Find the severity name for this level
    for severity, level in SEVERITY_HIERARCHY.items():
        if level == max_severity:
            return severity
    
    return "NA"
