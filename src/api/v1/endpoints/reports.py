"""
Report Generation endpoints for comprehensive health reports.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from src.utils.logging import logger
from src.auth.dependencies import CurrentUser
from src.agents.report_generator_agent import ReportGeneratorAgent
from src.agents.crew_agents.expert_crew import ExpertConsultationCrew
from src.db.neo4j_db import get_graph
from src.db.mongo_db import get_mongo
from src.db.milvus_db import get_milvus

router = APIRouter(tags=["reports"])


class ReportRequest(BaseModel):
    """Model for report generation requests."""
    report_type: str = Field(..., description="Type of report (comprehensive, summary, timeline, body_part)")
    title: str = Field(..., description="Report title")
    include_expert_opinion: bool = Field(True, description="Include expert medical opinion")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range for report (start_date, end_date)")
    body_part: Optional[str] = Field(None, description="Specific body part for focused report")
    format: str = Field("markdown", description="Report format (markdown, pdf)")


class ReportStatus(BaseModel):
    """Model for report status."""
    report_id: str = Field(description="Report identifier")
    status: str = Field(description="Generation status")
    progress: float = Field(description="Generation progress (0-100)")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    message: str = Field(description="Status message")


class ReportResponse(BaseModel):
    """Model for report response."""
    report_id: str = Field(description="Report identifier")
    title: str = Field(description="Report title")
    content: str = Field(description="Report content (markdown)")
    generated_at: str = Field(description="Generation timestamp")
    report_type: str = Field(description="Report type")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL for PDF")


@router.post("/generate", response_model=ReportResponse)
async def generate_health_report(
    request: ReportRequest,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks
):
    """
    Generate a comprehensive health report.
    
    Features:
    - Multiple report types (comprehensive, summary, timeline, body_part)
    - Expert opinion integration
    - PDF export capability
    - Background processing
    - Patient context integration
    """
    try:
        patient_id = current_user.patient_id
        report_id = f"report_{patient_id}_{int(datetime.utcnow().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Validate report type
        valid_types = ["comprehensive", "summary", "timeline", "body_part"]
        if request.report_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid report type. Must be one of: {valid_types}"
            )
        
        # Validate body part if specified
        if request.report_type == "body_part" and not request.body_part:
            raise HTTPException(
                status_code=400,
                detail="Body part must be specified for body_part report type"
            )
        
        # Parse date range
        start_date = None
        end_date = None
        if request.date_range:
            try:
                start_date = datetime.strptime(request.date_range.get("start_date", ""), "%Y-%m-%d")
                end_date = datetime.strptime(request.date_range.get("end_date", ""), "%Y-%m-%d")
            except (ValueError, KeyError):
                raise HTTPException(status_code=400, detail="Invalid date range format")
        
        # Initialize report generator
        report_generator = ReportGeneratorAgent()
        
        # Generate report
        report_data = await report_generator.generate_report(
            patient_id=patient_id,
            report_id=report_id,
            report_type=request.report_type,
            title=request.title,
            include_expert_opinion=request.include_expert_opinion,
            start_date=start_date,
            end_date=end_date,
            body_part=request.body_part
        )
        
        # Store report in database
        await store_report(patient_id, report_id, report_data, request)
        
        return ReportResponse(
            report_id=report_id,
            title=report_data.get("title", request.title),
            content=report_data.get("content", ""),
            generated_at=datetime.utcnow().isoformat(),
            report_type=request.report_type,
            file_size=len(report_data.get("content", "").encode('utf-8')),
            download_url=f"/api/v1/reports/download/{report_id}" if request.format == "pdf" else None
        )
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/status/{report_id}", response_model=ReportStatus)
async def get_report_status(report_id: str, current_user: CurrentUser):
    """
    Get status of a report generation.
    """
    try:
        patient_id = current_user.patient_id
        
        # Get report status from database
        mongo_client = await get_mongo()
        report_status = await mongo_client.get_report_status(patient_id, report_id)
        
        if not report_status:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return ReportStatus(
            report_id=report_id,
            status=report_status.get("status", "unknown"),
            progress=report_status.get("progress", 0.0),
            estimated_completion=report_status.get("estimated_completion"),
            message=report_status.get("message", "Report processing")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report status")


@router.get("/download/{report_id}")
async def download_report(report_id: str, current_user: CurrentUser, format: str = "pdf"):
    """
    Download a generated report in specified format.
    """
    try:
        patient_id = current_user.patient_id
        
        # Get report from database
        mongo_client = await get_mongo()
        report_data = await mongo_client.get_report(patient_id, report_id)
        
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        content = report_data.get("content", "")
        
        if format.lower() == "pdf":
            # Convert markdown to PDF
            from src.utils.pdf_generator import generate_pdf_from_markdown
            
            pdf_path = await generate_pdf_from_markdown(
                markdown_content=content,
                title=report_data.get("title", "Health Report"),
                filename=f"health_report_{report_id}.pdf"
            )
            
            return FileResponse(
                path=pdf_path,
                filename=f"health_report_{report_id}.pdf",
                media_type="application/pdf"
            )
        
        elif format.lower() == "markdown":
            # Return markdown content
            return StreamingResponse(
                iter([content]),
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename=health_report_{report_id}.md"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'pdf' or 'markdown'")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download report: {e}")
        raise HTTPException(status_code=500, detail="Failed to download report")


@router.get("/list")
async def list_reports(
    current_user: CurrentUser,
    limit: int = 20,
    skip: int = 0,
    report_type: Optional[str] = Query(None, description="Filter by report type")
):
    """
    List generated reports for the patient.
    """
    try:
        patient_id = current_user.patient_id
        
        # Get reports from database
        mongo_client = await get_mongo()
        reports = await mongo_client.get_reports(
            patient_id, 
            limit=limit, 
            skip=skip, 
            report_type=report_type
        )
        
        return {
            "reports": reports,
            "total_count": len(reports),
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports")


async def store_report(patient_id: str, report_id: str, report_data: Dict[str, Any], request: ReportRequest):
    """Store generated report in database."""
    try:
        mongo_client = await get_mongo()
        
        report_record = {
            "report_id": report_id,
            "patient_id": patient_id,
            "title": report_data.get("title", request.title),
            "content": report_data.get("content", ""),
            "report_type": request.report_type,
            "include_expert_opinion": request.include_expert_opinion,
            "date_range": request.date_range,
            "body_part": request.body_part,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "completed",
            "file_size": len(report_data.get("content", "").encode('utf-8'))
        }
        
        await mongo_client.store_report(patient_id, report_record)
        
    except Exception as e:
        logger.error(f"Failed to store report: {e}")


@router.get("/health")
async def get_reports_health():
    """Health check for reports service."""
    return {
        "status": "healthy",
        "service": "reports",
        "version": "1.0.0",
        "features": [
            "Comprehensive health reports",
            "Expert opinion integration",
            "PDF export",
            "Multiple report types",
            "Background processing",
            "Date range filtering",
            "Body part focused reports"
        ]
    } 