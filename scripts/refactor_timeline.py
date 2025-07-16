#!/usr/bin/env python3
"""
Script to refactor timeline.py from user_id to patient_id for HIPAA compliance.
"""

def refactor_timeline_endpoints():
    """Refactor timeline endpoints to use patient_id instead of user_id."""
    
    with open('/home/user/agents/meditwin-agents/src/api/endpoints/timeline.py', 'r') as f:
        content = f.read()
    
    # Replace user_id variable usage throughout the file
    replacements = [
        ('user_id = current_user.user_id', 'patient_id = current_user.patient_id'),
        ('mongo_events = await mongo_client.get_timeline_events(user_id,', 'mongo_events = await mongo_client.get_timeline_events(patient_id,'),
        ('neo4j_events = neo4j_client.get_patient_timeline(user_id,', 'neo4j_events = neo4j_client.get_patient_timeline(patient_id,'),
        ('"user_id": user_id,', '"patient_id": patient_id,'),
        ('user_id,', 'patient_id,'),
        ('user_id=user_id,', 'user_id=patient_id,'),  # Database methods still expect user_id parameter
        ('store_timeline_event(user_id,', 'store_timeline_event(patient_id,'),
        ('create_medical_event(user_id,', 'create_medical_event(patient_id,'),
        ('# Get user_id from JWT token', '# Get patient_id from JWT token'),
        ('Get chronological timeline of medical events for a user.', 'Get chronological timeline of medical events for a patient.'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Write back
    with open('/home/user/agents/meditwin-agents/src/api/endpoints/timeline.py', 'w') as f:
        f.write(content)
    
    print("✅ Successfully refactored timeline.py to use patient_id")

if __name__ == "__main__":
    refactor_timeline_endpoints()
