"""
Health data export endpoints for generating reports and downloads.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from src.auth.dependencies import CurrentUser
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph
from src.utils.report_generator import report_generator
from src.utils.logging import logger, log_user_action

router = APIRouter(tags=["export"])


@router.get("/health/export")
async def export_health_report(
    current_user: CurrentUser,
    format: str = Query("pdf", description="Export format (pdf, json)"),
    include_timeline: bool = Query(True, description="Include medical timeline"),
    timeline_days: int = Query(90, description="Days of timeline to include", ge=1, le=365)
):
    """
    Export comprehensive health report for the patient.
    
    Generates a PDF report containing:
    - Current health status
    - Body parts severity assessment  
    - Recent medical events timeline
    - Summary statistics
    """
    try:
        patient_id = current_user.patient_id
        
        # Gather health data
        logger.info(f"Generating health export for patient {patient_id[:8]}...")
        
        # Get body parts data
        neo4j_client = get_graph()
        neo4j_client.ensure_user_initialized(patient_id)
        severities = neo4j_client.get_body_part_severities(patient_id)
        
        body_parts_data = [
            {"name": body_part, "severity": severity}
            for body_part, severity in severities.items()
        ]
        
        timeline_events = []
        if include_timeline:
            # Get timeline events
            from datetime import timedelta
            
            mongo_client = await get_mongo()
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=timeline_days)
            
            # Fetch from both sources
            try:
                mongo_events = await mongo_client.get_timeline_events(
                    patient_id,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat()
                )
            except Exception as e:
                logger.warning(f"Failed to fetch MongoDB timeline: {e}")
                mongo_events = []
            
            try:
                neo4j_events = neo4j_client.get_patient_timeline(
                    patient_id,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat()
                )
            except Exception as e:
                logger.warning(f"Failed to fetch Neo4j timeline: {e}")
                neo4j_events = []
            
            # Combine and sort
            timeline_events = mongo_events + neo4j_events
            timeline_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Get patient profile (if available)
        patient_profile = None
        try:
            mongo_client = await get_mongo()
            # Try to get profile data - this might not exist yet
            profile_records = await mongo_client.get_medical_records(
                patient_id, 
                record_type="profile",
                limit=1
            )
            if profile_records:
                patient_profile = profile_records[0].get('data', {})
        except Exception as e:
            logger.debug(f"No profile data found: {e}")
        
        # Log the export action
        log_user_action(
            patient_id,
            "health_report_export",
            {
                "format": format,
                "include_timeline": include_timeline,
                "timeline_days": timeline_days,
                "body_parts_count": len(body_parts_data),
                "timeline_events_count": len(timeline_events)
            }
        )
        
        if format.lower() == "pdf":
            # Generate PDF report
            pdf_bytes = await report_generator.generate_health_report(
                patient_id=patient_id,
                body_parts_data=body_parts_data,
                timeline_events=timeline_events,
                patient_profile=patient_profile
            )
            
            # Return PDF as streaming response
            filename = f"health_report_{patient_id[:8]}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        elif format.lower() == "json":
            # Return structured JSON data
            export_data = {
                "patient_id": patient_id,
                "export_date": datetime.utcnow().isoformat(),
                "body_parts": body_parts_data,
                "timeline_events": timeline_events if include_timeline else [],
                "patient_profile": patient_profile,
                "summary": {
                    "total_body_parts": len(body_parts_data),
                    "total_timeline_events": len(timeline_events),
                    "timeline_period_days": timeline_days if include_timeline else 0,
                    "severity_breakdown": _calculate_severity_breakdown(body_parts_data)
                }
            }
            
            filename = f"health_data_{patient_id[:8]}_{datetime.now().strftime('%Y%m%d')}.json"
            
            return Response(
                content=str(export_data).encode(),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported format '{format}'. Supported: pdf, json"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export health report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate health report")


@router.get("/timeline/export")
async def export_timeline(
    current_user: CurrentUser,
    format: str = Query("json", description="Export format (json, csv)"),
    days: int = Query(365, description="Days of timeline to export", ge=1, le=1825),  # Max 5 years
    event_types: Optional[str] = Query(None, description="Filter by event types (comma-separated)")
):
    """
    Export medical timeline data.
    
    Exports medical events in structured format for external analysis.
    """
    try:
        patient_id = current_user.patient_id
        
        # Get timeline data
        from datetime import timedelta
        
        mongo_client = await get_mongo()
        neo4j_client = get_graph()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Parse event types filter
        event_type_list = None
        if event_types:
            event_type_list = [t.strip() for t in event_types.split(',')]
        
        # Fetch timeline data
        try:
            mongo_events = await mongo_client.get_timeline_events(
                patient_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                event_types=event_type_list
            )
        except Exception as e:
            logger.warning(f"MongoDB timeline fetch failed: {e}")
            mongo_events = []
        
        try:
            neo4j_events = neo4j_client.get_patient_timeline(
                patient_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
            # Filter by event types if specified
            if event_type_list:
                neo4j_events = [
                    e for e in neo4j_events 
                    if e.get('event_type') in event_type_list
                ]
        except Exception as e:
            logger.warning(f"Neo4j timeline fetch failed: {e}")
            neo4j_events = []
        
        # Combine and sort
        all_events = mongo_events + neo4j_events
        all_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Log export
        log_user_action(
            patient_id,
            "timeline_export",
            {
                "format": format,
                "days": days,
                "event_types": event_types,
                "total_events": len(all_events)
            }
        )
        
        filename_base = f"timeline_{patient_id[:8]}_{datetime.now().strftime('%Y%m%d')}"
        
        if format.lower() == "json":
            export_data = {
                "patient_id": patient_id,
                "export_date": datetime.utcnow().isoformat(),
                "period_days": days,
                "event_types_filter": event_type_list,
                "total_events": len(all_events),
                "events": all_events
            }
            
            return Response(
                content=str(export_data).encode(),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename_base}.json"}
            )
            
        elif format.lower() == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if all_events:
                # Get all possible field names
                fieldnames = set()
                for event in all_events:
                    fieldnames.update(event.keys())
                fieldnames = sorted(list(fieldnames))
                
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_events)
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content.encode(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename_base}.csv"}
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format '{format}'. Supported: json, csv"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timeline export failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to export timeline")


def _calculate_severity_breakdown(body_parts_data):
    """Calculate severity distribution for summary statistics."""
    breakdown = {}
    for part in body_parts_data:
        severity = part.get('severity', 'NA')
        breakdown[severity] = breakdown.get(severity, 0) + 1
    return breakdown
