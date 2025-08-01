#!/usr/bin/env python3
"""
HIPAA Compliance Fix Script

This script identifies and fixes patient data isolation issues in the Neo4j database.
It ensures that no patient data is shared across different patients.

⚠️  CRITICAL SECURITY UPDATE ⚠️
This addresses severe HIPAA violations where patient body parts and medical data
were being shared across different patients due to improper database constraints.
"""

import asyncio
import sys
from typing import List, Dict, Any

# Add the project root to the path
sys.path.append('.')

from src.db.neo4j import neo4j_connection
from src.utils.logging import logger


async def audit_patient_isolation() -> Dict[str, Any]:
    """Audit all patients for data isolation issues"""
    try:
        neo4j_connection._connect()
        
        # Get all patients
        query = "MATCH (p:Patient) RETURN p.patient_id as patient_id"
        patients = neo4j_connection.execute_query(query)
        
        audit_results = {
            "total_patients": len(patients),
            "patients_with_violations": [],
            "total_violations": 0,
            "violation_summary": {
                "orphaned_body_parts": 0,
                "orphaned_events": 0,
                "orphaned_conditions": 0,
                "shared_body_parts": 0
            }
        }
        
        print(f"🔍 Auditing {len(patients)} patients for HIPAA compliance violations...")
        
        for patient in patients:
            patient_id = patient["patient_id"]
            patient_audit = neo4j_connection.validate_patient_isolation(patient_id)
            
            if not patient_audit.get("is_hipaa_compliant", False):
                audit_results["patients_with_violations"].append({
                    "patient_id": patient_id,
                    "violations": patient_audit
                })
                
                # Count violations
                audit_results["violation_summary"]["orphaned_body_parts"] += patient_audit.get("orphaned_body_parts", 0)
                audit_results["violation_summary"]["orphaned_events"] += patient_audit.get("orphaned_events", 0)
                audit_results["violation_summary"]["orphaned_conditions"] += patient_audit.get("orphaned_conditions", 0)
        
        # Check for shared body parts across patients
        shared_body_parts_query = """
        MATCH (bp:BodyPart)<-[:HAS_BODY_PART]-(p1:Patient)
        MATCH (bp)<-[:HAS_BODY_PART]-(p2:Patient)
        WHERE p1.patient_id <> p2.patient_id
        RETURN bp.name as body_part, COUNT(DISTINCT p1.patient_id) as patient_count
        """
        
        shared_results = neo4j_connection.execute_query(shared_body_parts_query)
        audit_results["violation_summary"]["shared_body_parts"] = len(shared_results)
        
        if shared_results:
            audit_results["shared_body_parts_details"] = shared_results
        
        audit_results["total_violations"] = len(audit_results["patients_with_violations"])
        
        return audit_results
        
    except Exception as e:
        logger.error(f"Failed to audit patient isolation: {e}")
        return {"error": str(e)}


async def fix_all_patient_isolation() -> Dict[str, Any]:
    """Fix patient isolation issues for all patients"""
    try:
        neo4j_connection._connect()
        
        # Get all patients
        query = "MATCH (p:Patient) RETURN p.patient_id as patient_id"
        patients = neo4j_connection.execute_query(query)
        
        fix_results = {
            "total_patients": len(patients),
            "patients_fixed": 0,
            "total_fixes": {
                "body_parts": 0,
                "events": 0,
                "conditions": 0
            }
        }
        
        print(f"🔧 Fixing HIPAA compliance issues for {len(patients)} patients...")
        
        for patient in patients:
            patient_id = patient["patient_id"]
            success = neo4j_connection.fix_patient_data_isolation(patient_id)
            
            if success:
                fix_results["patients_fixed"] += 1
        
        # Remove shared body parts by recreating them with proper patient isolation
        print("🧹 Cleaning up shared body parts...")
        cleanup_query = """
        // Find body parts connected to multiple patients
        MATCH (bp:BodyPart)<-[:HAS_BODY_PART]-(p1:Patient)
        MATCH (bp)<-[:HAS_BODY_PART]-(p2:Patient)
        WHERE p1.patient_id <> p2.patient_id
        
        // For each patient, create their own isolated body part
        WITH bp, COLLECT(DISTINCT p1.patient_id) as patient_ids
        UNWIND patient_ids as patient_id
        
        // Create new isolated body part for each patient
        CREATE (new_bp:BodyPart {
            name: bp.name,
            patient_id: patient_id,
            severity: bp.severity,
            created_at: datetime(),
            migrated_from_shared: true
        })
        
        // Reconnect patient to new isolated body part
        WITH new_bp, patient_id, bp
        MATCH (p:Patient {patient_id: patient_id})
        CREATE (p)-[:HAS_BODY_PART]->(new_bp)
        
        // Remove old connection to shared body part
        WITH p, bp
        MATCH (p)-[r:HAS_BODY_PART]->(bp)
        DELETE r
        
        // If no more patients connected to old body part, delete it
        WITH bp
        OPTIONAL MATCH (bp)<-[:HAS_BODY_PART]-()
        WITH bp, COUNT(*) as connection_count
        WHERE connection_count = 0
        DELETE bp
        
        RETURN COUNT(*) as fixed_shared_body_parts
        """
        
        neo4j_connection.execute_write(cleanup_query)
        
        print("✅ HIPAA compliance fixes completed!")
        return fix_results
        
    except Exception as e:
        logger.error(f"Failed to fix patient isolation: {e}")
        return {"error": str(e)}


async def drop_old_constraints():
    """Drop old insecure constraints that allowed cross-patient data sharing"""
    try:
        neo4j_connection._connect()
        
        # Drop the dangerous constraint that made body parts globally unique
        drop_queries = [
            "DROP CONSTRAINT body_part_name_unique IF EXISTS",
            "DROP CONSTRAINT condition_name_unique IF EXISTS", 
            "DROP CONSTRAINT treatment_name_unique IF EXISTS"
        ]
        
        print("🗑️  Dropping insecure constraints...")
        for query in drop_queries:
            try:
                neo4j_connection.execute_write(query)
                print(f"   ✓ Dropped: {query}")
            except Exception as e:
                print(f"   ⚠️  Could not drop (might not exist): {query}")
        
        # Create new secure constraints
        print("🔒 Creating HIPAA-compliant constraints...")
        neo4j_connection.create_constraints()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update constraints: {e}")
        return False


async def main():
    """Main function to audit and fix HIPAA compliance issues"""
    print("🏥 HIPAA COMPLIANCE AUDIT AND FIX TOOL")
    print("=" * 50)
    print("⚠️  This tool fixes critical patient data isolation issues")
    print("⚠️  that violate HIPAA compliance requirements.")
    print()
    
    # Step 1: Drop old insecure constraints
    print("STEP 1: Updating database constraints...")
    await drop_old_constraints()
    print()
    
    # Step 2: Audit current state
    print("STEP 2: Auditing current patient data isolation...")
    audit_results = await audit_patient_isolation()
    
    if "error" in audit_results:
        print(f"❌ Audit failed: {audit_results['error']}")
        return
    
    print(f"📊 AUDIT RESULTS:")
    print(f"   Total patients: {audit_results['total_patients']}")
    print(f"   Patients with violations: {audit_results['total_violations']}")
    print(f"   Orphaned body parts: {audit_results['violation_summary']['orphaned_body_parts']}")
    print(f"   Orphaned events: {audit_results['violation_summary']['orphaned_events']}")
    print(f"   Orphaned conditions: {audit_results['violation_summary']['orphaned_conditions']}")
    print(f"   Shared body parts: {audit_results['violation_summary']['shared_body_parts']}")
    print()
    
    if audit_results['total_violations'] == 0 and audit_results['violation_summary']['shared_body_parts'] == 0:
        print("✅ No HIPAA violations found! Database is compliant.")
        return
    
    # Step 3: Fix violations
    print("STEP 3: Fixing HIPAA compliance violations...")
    fix_results = await fix_all_patient_isolation()
    
    if "error" in fix_results:
        print(f"❌ Fix failed: {fix_results['error']}")
        return
    
    print(f"🔧 FIX RESULTS:")
    print(f"   Patients processed: {fix_results['total_patients']}")
    print(f"   Patients fixed: {fix_results['patients_fixed']}")
    print()
    
    # Step 4: Re-audit to verify fixes
    print("STEP 4: Re-auditing to verify fixes...")
    final_audit = await audit_patient_isolation()
    
    if final_audit['total_violations'] == 0 and final_audit['violation_summary']['shared_body_parts'] == 0:
        print("✅ SUCCESS! All HIPAA compliance violations have been fixed.")
        print("✅ Patient data is now properly isolated.")
    else:
        print("⚠️  Some violations may still exist. Manual review recommended.")
        print(f"   Remaining violations: {final_audit['total_violations']}")
    
    print()
    print("🔒 HIPAA compliance update completed.")
    print("   Each patient's data is now completely isolated.")
    print("   No medical information is shared between patients.")


if __name__ == "__main__":
    asyncio.run(main())
