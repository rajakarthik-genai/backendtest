#!/usr/bin/env python3
"""
Script to refactor upload.py from user_id to patient_id for HIPAA compliance.
"""

def refactor_upload_endpoints():
    """Refactor upload endpoints to use patient_id instead of user_id."""
    
    with open('/home/user/agents/meditwin-agents/src/api/endpoints/upload.py', 'r') as f:
        content = f.read()
    
    # Replace all user_id parameter declarations with patient_id
    content = content.replace('user_id: AuthenticatedUserId', 'patient_id: AuthenticatedPatientId')
    
    # Replace user_id variable usage in function calls and data structures
    # Need to be careful to preserve the structure
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        # Replace user_id in function parameters and variable assignments
        if 'user_id=' in line:
            line = line.replace('user_id=user_id', 'user_id=patient_id')
        if '"user_id": user_id' in line:
            line = line.replace('"user_id": user_id', '"patient_id": patient_id')
        if 'user_id,' in line and 'def ' not in line:
            line = line.replace('user_id,', 'patient_id,')
        if 'user_id: str,' in line:
            line = line.replace('user_id: str,', 'patient_id: str,')
        if 'user_id: User identifier' in line:
            line = line.replace('user_id: User identifier', 'patient_id: Patient identifier (HIPAA-compliant)')
        if 'user_id: User' in line and 'identifier' in line:
            line = line.replace('user_id: User', 'patient_id: Patient')
        # Handle metadata access patterns
        if '.get("user_id")' in line:
            line = line.replace('.get("user_id")', '.get("patient_id")')
        
        updated_lines.append(line)
    
    content = '\n'.join(updated_lines)
    
    # Write back
    with open('/home/user/agents/meditwin-agents/src/api/endpoints/upload.py', 'w') as f:
        f.write(content)
    
    print("✅ Successfully refactored upload.py to use patient_id")

if __name__ == "__main__":
    refactor_upload_endpoints()
