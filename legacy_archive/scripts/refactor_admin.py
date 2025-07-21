#!/usr/bin/env python3
"""
Script to refactor admin.py from user_id to patient_id terminology for HIPAA compliance.
"""

import re

def refactor_admin_endpoints():
    """Refactor admin endpoints to use patient_id instead of user_id."""
    
    # Read the current file
    with open('/home/user/agents/meditwin-agents/src/api/endpoints/admin.py', 'r') as f:
        content = f.read()
    
    # Replace variable names and endpoint paths
    replacements = [
        # Endpoint paths
        (r'/users/', '/patients/'),
        
        # Function names
        (r'list_mongo_users', 'list_mongo_patients'),
        (r'list_neo4j_users', 'list_neo4j_patients'),
        (r'list_milvus_users', 'list_milvus_patients'),
        (r'list_all_users', 'list_all_patients'),
        (r'get_user_mongo_data', 'get_patient_mongo_data'),
        (r'get_user_neo4j_data', 'get_patient_neo4j_data'),
        (r'get_user_milvus_data', 'get_patient_milvus_data'),
        (r'get_user_all_data', 'get_patient_all_data'),
        (r'delete_user_data', 'delete_patient_data'),
        
        # URL parameters
        (r'/user/\{user_id\}', '/patient/{patient_id}'),
        (r'user_id: str', 'patient_id: str'),
        
        # Variable assignments and references
        (r'user_ids =', 'patient_ids ='),
        (r'user_ids,', 'patient_ids,'),
        (r'user_ids\)', 'patient_ids)'),
        (r'mongo_users =', 'mongo_patients ='),
        (r'neo4j_users =', 'neo4j_patients ='),
        (r'milvus_users =', 'milvus_patients ='),
        
        # Function parameters
        (r'async def [^(]+\(([^)]*?)user_id:', r'async def \1(patient_id:'),
        
        # Comments and docstrings
        (r'user IDs', 'patient IDs'),
        (r'user data', 'patient data'),
        (r'user-specific', 'patient-specific'),
        (r'MongoDB users', 'MongoDB patients'),
        (r'Neo4j users', 'Neo4j patients'),
        (r'Milvus users', 'Milvus patients'),
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        if r'async def' in pattern:
            # Handle function definitions specially
            content = re.sub(pattern, replacement, content)
        else:
            content = content.replace(pattern, replacement)
    
    # Handle remaining user_id references in the function bodies
    # Need to be more careful here to avoid breaking logic
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        # Replace user_id variable usage but preserve method calls like list_user_ids()
        if 'user_id' in line and 'list_user_ids' not in line and 'get_user_pii' not in line and 'delete_user_data' not in line:
            # Replace user_id variable references
            line = re.sub(r'\buser_id\b(?!\s*=\s*[a-zA-Z_])', 'patient_id', line)
        
        updated_lines.append(line)
    
    content = '\n'.join(updated_lines)
    
    # Write back
    with open('/home/user/agents/meditwin-agents/src/api/endpoints/admin.py', 'w') as f:
        f.write(content)
    
    print("✅ Successfully refactored admin.py to use patient_id")

if __name__ == "__main__":
    refactor_admin_endpoints()
