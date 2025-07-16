#!/usr/bin/env python3
"""
Comprehensive script to refactor all agent files from user_id to patient_id for HIPAA compliance.
"""

import os
import re

def refactor_agent_files():
    """Refactor all agent files to use patient_id instead of user_id."""
    
    agent_files = [
        'src/agents/crew_agents/medical_crew.py',
        'src/agents/base_specialist.py',
        'src/agents/aggregator_agent.py',
        'src/agents/cardiologist_agent.py',
        'src/agents/general_physician_agent.py',
        'src/agents/neurologist_agent.py',
        'src/agents/orthopedist_agent.py',
        'src/agents/timeline_builder_agent.py',
        'src/agents/ingestion_agent.py',
        'src/agents/orchestrator_agent.py',
        'src/agents/expert_router.py'
    ]
    
    for file_path in agent_files:
        if os.path.exists(file_path):
            print(f"Processing {file_path}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Replace function parameter declarations
            content = re.sub(r'user_id: str,', 'patient_id: str,', content)
            content = re.sub(r'user_id: str\)', 'patient_id: str)', content)
            
            # Replace function parameter usage but preserve database method calls
            # Database methods may still expect user_id as parameter name
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                # Replace user_id variable references in agent functions
                if ('user_id:' in line or 'user_id =' in line or 
                    'user_id,' in line or '(user_id' in line or 
                    'user_id)' in line):
                    
                    # Don't replace in database method definitions or calls that expect user_id param
                    if not any(skip in line for skip in [
                        'def get_', 'def list_', 'def store_', 'def create_',
                        '.get_', '.list_', '.store_', '.create_', '.delete_',
                        'mongo_client.', 'neo4j_client.', 'milvus_client.'
                    ]):
                        # Replace user_id with patient_id in agent logic
                        line = re.sub(r'\buser_id\b', 'patient_id', line)
                
                # Update docstring parameters
                if 'user_id: Patient identifier' in line:
                    line = line.replace('user_id: Patient identifier', 'patient_id: HIPAA-compliant patient identifier')
                elif 'user_id: User identifier' in line:
                    line = line.replace('user_id: User identifier', 'patient_id: HIPAA-compliant patient identifier')
                
                # Update comments
                if '# Get user_id' in line:
                    line = line.replace('# Get user_id', '# Get patient_id')
                
                updated_lines.append(line)
            
            content = '\n'.join(updated_lines)
            
            # Write back only if content changed
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"✅ Updated {file_path}")
            else:
                print(f"⚪ No changes needed for {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

def refactor_remaining_endpoints():
    """Refactor remaining endpoint files."""
    
    endpoint_files = [
        'src/api/endpoints/events.py',
        'src/api/endpoints/chat.py',
        'src/api/endpoints/anatomy.py',
        'src/api/endpoints/documents.py',
        'src/api/endpoints/expert_opinion.py',
        'src/api/endpoints/tools.py',
        'src/api/endpoints/openai_compatible.py',
        'src/api/endpoints/openai_compat.py'
    ]
    
    for file_path in endpoint_files:
        if os.path.exists(file_path):
            print(f"Processing {file_path}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Replace import statements
            if 'AuthenticatedUserId' in content:
                content = content.replace('AuthenticatedUserId', 'AuthenticatedPatientId')
            
            # Replace parameter declarations
            content = re.sub(r'user_id: AuthenticatedUserId', 'patient_id: AuthenticatedPatientId', content)
            content = re.sub(r'user_id: str', 'patient_id: str', content)
            
            # Replace variable usage
            content = re.sub(r'current_user\.user_id', 'current_user.patient_id', content)
            
            # Handle specific patterns
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                # Replace user_id usage but preserve database calls
                if ('user_id' in line and 
                    not any(skip in line for skip in ['.get_', '.list_', '.store_', '.create_', '.delete_'])):
                    line = re.sub(r'\buser_id\b', 'patient_id', line)
                
                updated_lines.append(line)
            
            content = '\n'.join(updated_lines)
            
            # Write back only if content changed
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"✅ Updated {file_path}")
            else:
                print(f"⚪ No changes needed for {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

if __name__ == "__main__":
    print("🔄 Starting comprehensive refactor to patient_id...")
    refactor_agent_files()
    refactor_remaining_endpoints()
    print("✅ Refactor complete!")
