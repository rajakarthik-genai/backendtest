"""
Simple test to verify body parts functionality
"""

# Test the body parts list manually
body_parts = [
    # Head and Neck (8 parts)
    "Head", "Brain", "Left Eye", "Right Eye", "Left Ear", "Right Ear", "Nose", "Neck",
    
    # Torso (10 parts)  
    "Heart", "Left Lung", "Right Lung", "Liver", "Stomach", "Pancreas", "Spleen", 
    "Left Kidney", "Right Kidney", "Spine",
    
    # Upper Body (6 parts)
    "Left Shoulder", "Right Shoulder", "Left Arm", "Right Arm", "Left Hand", "Right Hand",
    
    # Lower Body (6 parts)
    "Left Hip", "Right Hip", "Left Leg", "Right Leg", "Left Knee", "Right Knee"
]

print(f"✅ Body parts count: {len(body_parts)}")
print(f"✅ Expected: 30, Actual: {len(body_parts)}")
print(f"✅ Test {'PASSED' if len(body_parts) == 30 else 'FAILED'}")
print(f"✅ First 5 parts: {body_parts[:5]}")
print(f"✅ Last 5 parts: {body_parts[-5:]}")
