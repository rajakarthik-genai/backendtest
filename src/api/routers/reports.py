"""
Report generation endpoints
Handles comprehensive medical reports with visualizations
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
from datetime import datetime
import logging

from src.api.dependencies import get_current_user, get_db_clients, require_patient_access
from src.auth.dependencies import get_authenticated_patient_id, AuthenticatedPatientId
from src.models.report import ReportRequest, ReportResponse
from src.core.config import settings
from src.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=ReportResponse)
@limiter.limit("50/hour")
async def generate_medical_report(
    request: Request,
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients),
    _: str = Depends(require_patient_access)
):
    """
    Generate comprehensive medical reports with visualizations.
    Uses expert opinion system and all available patient data.
    """
    try:
        if not db_clients.get("mongodb"):
            raise HTTPException(status_code=503, detail="MongoDB not available")
        report_id = f"report_{report_request.patient_id}_{uuid.uuid4().hex[:8]}"
        
        if report_request.format == "pdf":
            # Queue PDF generation as background task
            await _queue_pdf_generation(
                report_id=report_id,
                report_request=report_request,
                db_clients=db_clients
            )
            
            return ReportResponse(
                report_id=report_id,
                status="generating",
                estimated_time=45,
                download_url=f"/api/v1/reports/download/{report_id}",
                preview_url=f"/api/v1/reports/preview/{report_id}",
                message="Report generation initiated. Use status endpoint to track progress."
            )
        
        else:
            # Generate markdown/HTML immediately
            report_content = await _generate_report_content(
                report_request=report_request,
                db_clients=db_clients
            )
            
            # Save report to database
            report_record = {
                "report_id": report_id,
                "patient_id": report_request.patient_id,
                "report_type": report_request.report_type,
                "format": report_request.format,
                "content": report_content,
                "generated_at": datetime.utcnow(),
                "generated_by": current_user["user_id"],
                "metadata": {
                    "include_visualizations": report_request.include_visualizations,
                    "include_recommendations": report_request.include_recommendations,
                    "focus_body_parts": report_request.focus_body_parts,
                    "time_range": report_request.time_range
                }
            }
            
            await db_clients["mongodb"].reports.insert_one(report_record)
            
            return JSONResponse(content={
                "report_id": report_id,
                "format": report_request.format,
                "content": report_content,
                "generated_at": datetime.utcnow().isoformat(),
                "patient_id": report_request.patient_id,
                "metadata": {
                    "total_sections": len(report_content.split("##")) - 1,
                    "report_type": report_request.report_type,
                    "word_count": len(report_content.split())
                }
            })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_medical_report: {e}")
        raise HTTPException(status_code=503, detail="Database error")

@router.get("/status/{report_id}")
@limiter.limit("1000/hour")
async def get_report_status(
    request: Request,
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get report generation status
    """
    try:
        if not db_clients.get("mongodb"):
            raise HTTPException(status_code=503, detail="MongoDB not available")
        # Get report from database
        report = await db_clients["mongodb"].reports.find_one({"report_id": report_id})
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Check access permission
        if report["patient_id"] != current_user.get("patient_id") and not current_user.get("is_provider"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "report_id": report_id,
            "status": report.get("status", "completed"),
            "progress": report.get("progress", 100),
            "generated_at": report.get("generated_at"),
            "format": report.get("format"),
            "download_url": f"/api/v1/reports/download/{report_id}" if report.get("status") == "completed" else None,
            "error_message": report.get("error_message")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_report_status: {e}")
        raise HTTPException(status_code=503, detail="Database error")

@router.get("/download/{report_id}")
@limiter.limit("100/hour")
async def download_report(
    request: Request,
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Download generated report
    """
    try:
        if not db_clients.get("mongodb"):
            raise HTTPException(status_code=503, detail="MongoDB not available")
        # Get report from database
        report = await db_clients["mongodb"].reports.find_one({"report_id": report_id})
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Check access permission
        if report["patient_id"] != current_user.get("patient_id") and not current_user.get("is_provider"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if report.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Report not ready for download")
        
        # Return report content
        return {
            "report_id": report_id,
            "patient_id": report["patient_id"],
            "format": report["format"],
            "content": report["content"],
            "generated_at": report["generated_at"],
            "metadata": report.get("metadata", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download_report: {e}")
        raise HTTPException(status_code=503, detail="Database error")

@router.get("/list")
@limiter.limit("1000/hour")
async def list_patient_reports(
    request: Request,
    limit: int = 20,
    skip: int = 0,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    List all reports for a patient
    """
    try:
        if not db_clients.get("mongodb"):
            raise HTTPException(status_code=503, detail="MongoDB not available")
        # Get reports from database
        cursor = db_clients["mongodb"].reports.find(
            {"patient_id": patient_id}
        ).sort("generated_at", -1).skip(skip).limit(limit)
        
        reports = await cursor.to_list(length=limit)
        
        # Format response
        report_list = []
        for report in reports:
            report_list.append({
                "report_id": report["report_id"],
                "report_type": report["report_type"],
                "format": report["format"],
                "status": report.get("status", "completed"),
                "generated_at": report["generated_at"],
                "generated_by": report.get("generated_by"),
                "download_url": f"/api/v1/reports/download/{report['report_id']}" if report.get("status") == "completed" else None
            })
        
        return {
            "patient_id": patient_id,
            "reports": report_list,
            "total": await db_clients["mongodb"].reports.count_documents({"patient_id": patient_id})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in list_patient_reports: {e}")
        raise HTTPException(status_code=503, detail="Database error")

# Helper functions

async def _queue_pdf_generation(report_id: str, report_request: ReportRequest, db_clients: dict):
    """Queue PDF generation as background job"""
    try:
        if not db_clients.get("mongodb"):
            raise HTTPException(status_code=503, detail="MongoDB not available")
        # Create initial report record
        report_record = {
            "report_id": report_id,
            "patient_id": report_request.patient_id,
            "report_type": report_request.report_type,
            "format": "pdf",
            "status": "generating",
            "progress": 0,
            "generated_at": datetime.utcnow(),
            "metadata": {
                "include_visualizations": report_request.include_visualizations,
                "include_recommendations": report_request.include_recommendations,
                "focus_body_parts": report_request.focus_body_parts,
                "time_range": report_request.time_range
            }
        }
        
        await db_clients["mongodb"].reports.insert_one(report_record)
        
        # Queue background job
        await db_clients["redis"].enqueue_job({
            "job_type": "pdf_report_generation",
            "job_id": f"pdf_{report_id}",
            "report_id": report_id,
            "report_request": report_request.dict()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue PDF generation: {e}")
        raise HTTPException(status_code=503, detail="Database error")

async def _generate_report_content(report_request: ReportRequest, db_clients: dict) -> str:
    """Generate report content in markdown format"""
    try:
        if not db_clients.get("mongodb"):
            raise HTTPException(status_code=503, detail="MongoDB not available")
        # Get patient data
        patient_id = report_request.patient_id
        
        # Get documents
        cursor = db_clients["mongodb"].documents.find(
            {"patient_id": patient_id, "status": "completed"}
        ).sort("uploaded_at", -1)
        
        documents = await cursor.to_list(length=None)
        
        # Get health data from Neo4j
        neo4j = db_clients["neo4j"]
        
        # Get conditions
        conditions_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_CONDITION]->(c:Condition)
            RETURN c.name as name, c.severity as severity, c.status as status, c.diagnosed_date as date
            ORDER BY c.severity DESC
        """, {"patient_id": patient_id})
        
        # Get timeline events
        timeline_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(ev:Event)
            OPTIONAL MATCH (ev)-[:AFFECTS]->(bp:BodyPart)
            RETURN ev.date as date, ev.event_type as type, ev.description as description, bp.name as body_part
            ORDER BY ev.date DESC
            LIMIT 20
        """, {"patient_id": patient_id})
        
        # Generate report content
        content = f"""# Medical Report - Patient {patient_id}

## Report Summary
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Type**: {report_request.report_type.title()}
- **Period**: {report_request.time_range or 'All Time'}
- **Documents Analyzed**: {len(documents)}

## Health Overview

### Medical Documents
"""
        
        for doc in documents[:10]:  # Show recent 10 documents
            content += f"- **{doc['filename']}** ({doc['uploaded_at'].strftime('%Y-%m-%d')})\n"
        
        content += "\n### Active Conditions\n"
        
        active_conditions = [c for c in conditions_result if c.get("status") == "active"]
        if active_conditions:
            for condition in active_conditions:
                severity = condition.get("severity", 0)
                content += f"- **{condition['name']}** (Severity: {severity}/10)\n"
        else:
            content += "- No active conditions recorded\n"
        
        content += "\n### Recent Medical Events\n"
        
        if timeline_result:
            for event in timeline_result[:10]:
                date_str = event.get("date", "Unknown date")
                if isinstance(date_str, datetime):
                    date_str = date_str.strftime('%Y-%m-%d')
                content += f"- **{date_str}**: {event.get('description', 'No description')} ({event.get('type', 'Unknown type')})\n"
        else:
            content += "- No recent events recorded\n"
        
        if report_request.include_recommendations:
            content += """
## Recommendations

### General Health Maintenance
1. Continue regular check-ups with healthcare providers
2. Maintain current medication regimen as prescribed
3. Monitor symptoms and report any changes
4. Follow up on any pending test results

### Preventive Care
1. Stay up to date with routine screenings
2. Maintain healthy lifestyle habits
3. Consider discussing family history with providers
4. Keep medical records organized and accessible

"""
        
        content += """
## Next Steps
- Schedule follow-up appointments as recommended
- Complete any pending medical tests
- Review medication list with healthcare provider
- Update emergency contacts and medical information

---
*This report was generated using AI analysis of medical records. 
Please consult with your healthcare provider for medical decisions.*
"""
        
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report content generation failed: {e}")
        return f"# Error Generating Report\n\nUnable to generate report content: {str(e)}"
