"""
Health data export endpoints for generating PDF reports and other export formats.
Provides comprehensive patient data exports in various formats.
"""

import tempfile
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from io import BytesIO

from src.auth.dependencies import CurrentUser
from src.utils.logging import logger, log_user_action

router = APIRouter(tags=["health-export"])


@router.get("/export")
async def export_health_data_pdf(
    current_user: CurrentUser,
    include_timeline: bool = Query(True, description="Include medical timeline"),
    include_body_parts: bool = Query(True, description="Include body part severities"),
    include_chat_summary: bool = Query(False, description="Include recent chat summary"),
    date_range_days: int = Query(365, description="Number of days of history to include", ge=30, le=1095)
):
    """
    Export comprehensive health data as a PDF report.
    
    Generates a PDF containing:
    - Patient overview and current health status
    - Body part severity analysis with 3D visualization data
    - Medical timeline of events
    - Optional chat interaction summary
    - Generated insights and recommendations
    """
    try:
        patient_id = current_user.patient_id
        
        logger.info(f"Starting PDF export for patient {patient_id[:8]}...")
        
        # Collect all data for the report
        report_data = await _collect_export_data(
            patient_id,
            include_timeline,
            include_body_parts, 
            include_chat_summary,
            date_range_days
        )
        
        # Generate PDF
        pdf_buffer = await _generate_health_pdf(patient_id, report_data)
        
        # Log the action
        log_user_action(
            patient_id,
            "health_data_exported",
            {
                "export_format": "pdf",
                "include_timeline": include_timeline,
                "include_body_parts": include_body_parts,
                "include_chat_summary": include_chat_summary,
                "date_range_days": date_range_days,
                "report_size_kb": len(pdf_buffer) // 1024
            }
        )
        
        # Return PDF as download
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"health_report_{patient_id[:8]}_{timestamp}.pdf"
        
        return Response(
            content=pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export health data: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate health data export")


@router.get("/export/json")
async def export_health_data_json(
    current_user: CurrentUser,
    include_timeline: bool = Query(True, description="Include medical timeline"),
    include_body_parts: bool = Query(True, description="Include body part severities"),
    include_chat_summary: bool = Query(False, description="Include recent chat summary"),
    date_range_days: int = Query(365, description="Number of days of history to include", ge=30, le=1095)
):
    """
    Export comprehensive health data as structured JSON.
    
    Returns the same data as PDF export but in machine-readable JSON format.
    Useful for data portability and integration with other systems.
    """
    try:
        patient_id = current_user.patient_id
        
        # Collect all data for export
        report_data = await _collect_export_data(
            patient_id,
            include_timeline,
            include_body_parts,
            include_chat_summary,
            date_range_days
        )
        
        # Add export metadata
        report_data["export_info"] = {
            "exported_at": datetime.utcnow().isoformat(),
            "export_format": "json",
            "patient_id": patient_id,
            "date_range_days": date_range_days,
            "generated_by": "MediTwin Health Platform"
        }
        
        # Log the action
        log_user_action(
            patient_id,
            "health_data_exported",
            {
                "export_format": "json",
                "include_timeline": include_timeline,
                "include_body_parts": include_body_parts,
                "include_chat_summary": include_chat_summary,
                "date_range_days": date_range_days,
                "data_size_kb": len(str(report_data)) // 1024
            }
        )
        
        return report_data
        
    except Exception as e:
        logger.error(f"Failed to export health data as JSON: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate JSON export")


async def _collect_export_data(
    patient_id: str,
    include_timeline: bool,
    include_body_parts: bool,
    include_chat_summary: bool,
    date_range_days: int
) -> dict:
    """Collect all data needed for export."""
    
    report_data = {
        "patient_id": patient_id,
        "generated_at": datetime.utcnow().isoformat(),
        "date_range_days": date_range_days
    }
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=date_range_days)
    
    # Get body parts data if requested
    if include_body_parts:
        try:
            from src.db.neo4j_db import get_graph
            
            neo4j_client = await get_graph()
            severities = await neo4j_client.get_body_part_severities(patient_id)
            
            body_parts_data = []
            for body_part, severity in severities.items():
                if not body_part.endswith("_last_updated") and not body_part.endswith("_event_count"):
                    body_parts_data.append({
                        "name": body_part,
                        "severity": severity,
                        "last_updated": severities.get(f"{body_part}_last_updated"),
                        "event_count": severities.get(f"{body_part}_event_count", 0)
                    })
            
            report_data["body_parts"] = {
                "total_parts": len(body_parts_data),
                "parts": body_parts_data,
                "severity_summary": _calculate_severity_summary(body_parts_data)
            }
            
        except Exception as e:
            logger.warning(f"Failed to collect body parts data: {e}")
            report_data["body_parts"] = {"error": str(e)}
    
    # Get timeline data if requested
    if include_timeline:
        try:
            from src.db.mongo_db import get_mongo
            from src.db.neo4j_db import get_graph
            
            mongo_client = await get_mongo()
            neo4j_client = await get_graph()
            
            # Get events from both sources
            mongo_events = await mongo_client.get_timeline_events(
                patient_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=200
            )
            
            neo4j_events = await neo4j_client.get_patient_timeline(
                patient_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
            
            # Combine events
            all_events = []
            for event in mongo_events:
                all_events.append({**event, "source": "mongodb"})
            for event in neo4j_events:
                all_events.append({**event, "source": "neo4j"})
            
            # Sort by timestamp
            all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            report_data["timeline"] = {
                "total_events": len(all_events),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "events": all_events[:100],  # Limit for export size
                "event_summary": _calculate_event_summary(all_events)
            }
            
        except Exception as e:
            logger.warning(f"Failed to collect timeline data: {e}")
            report_data["timeline"] = {"error": str(e)}
    
    # Get chat summary if requested
    if include_chat_summary:
        try:
            from src.db.redis_db import get_redis
            
            redis_client = await get_redis()
            
            # Get recent chat history (last 7 days)
            chat_history = await redis_client.get_chat_history(patient_id, limit=50)
            
            if chat_history:
                report_data["chat_summary"] = {
                    "total_messages": len(chat_history),
                    "recent_interactions": chat_history[:10],  # Last 10 interactions
                    "summary": "Recent chat interactions with AI assistant included"
                }
            else:
                report_data["chat_summary"] = {
                    "total_messages": 0,
                    "summary": "No recent chat interactions found"
                }
                
        except Exception as e:
            logger.warning(f"Failed to collect chat summary: {e}")
            report_data["chat_summary"] = {"error": str(e)}
    
    return report_data


def _calculate_severity_summary(body_parts_data: list) -> dict:
    """Calculate summary statistics for body part severities."""
    severity_counts = {}
    total_events = 0
    
    for part in body_parts_data:
        severity = part.get("severity", "NA")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        total_events += part.get("event_count", 0)
    
    # Find worst severity
    severity_order = ["NA", "normal", "mild", "moderate", "severe", "critical"]
    worst_severity = "NA"
    
    for severity in reversed(severity_order):
        if severity_counts.get(severity, 0) > 0:
            worst_severity = severity
            break
    
    return {
        "by_severity": severity_counts,
        "worst_severity": worst_severity,
        "total_events_all_parts": total_events,
        "parts_with_issues": sum(1 for part in body_parts_data if part.get("severity") not in ["NA", "normal"])
    }


def _calculate_event_summary(events: list) -> dict:
    """Calculate summary statistics for timeline events."""
    summary = {
        "by_type": {},
        "by_severity": {},
        "by_source": {},
        "recent_count": 0
    }
    
    recent_threshold = datetime.utcnow() - timedelta(days=30)
    
    for event in events:
        # Count by type
        event_type = event.get("type", "unknown")
        summary["by_type"][event_type] = summary["by_type"].get(event_type, 0) + 1
        
        # Count by severity
        severity = event.get("severity", "unknown")
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        # Count by source
        source = event.get("source", "unknown")
        summary["by_source"][source] = summary["by_source"].get(source, 0) + 1
        
        # Count recent events (last 30 days)
        timestamp = event.get("timestamp", "")
        if timestamp:
            try:
                event_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if event_date > recent_threshold:
                    summary["recent_count"] += 1
            except:
                pass
    
    return summary


async def _generate_health_pdf(patient_id: str, report_data: dict) -> bytes:
    """Generate PDF report from collected data."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import black, blue, red, green, orange
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom title style (avoid conflicts)
        try:
            title_style = ParagraphStyle(
                'CustomMediTwinTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=blue
            )
        except:
            # Fallback if style already exists
            title_style = styles['Heading1']
        
        # Build story
        story = []
        
        # Title page
        story.append(Paragraph("Medical Health Report", title_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Patient ID: {patient_id[:8]}****", styles['Heading2']))
        story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        
        summary_text = f"""
        This comprehensive health report covers {report_data.get('date_range_days', 365)} days of medical data.
        The report includes body part severity analysis, medical event timeline, and health insights.
        """
        
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Body Parts Section
        if "body_parts" in report_data and "error" not in report_data["body_parts"]:
            story.append(PageBreak())
            story.append(Paragraph("Body Part Analysis", styles['Heading2']))
            
            body_parts_data = report_data["body_parts"]
            severity_summary = body_parts_data.get("severity_summary", {})
            
            # Summary stats
            story.append(Paragraph(f"Total Body Parts Monitored: {body_parts_data.get('total_parts', 0)}", styles['Normal']))
            story.append(Paragraph(f"Parts with Issues: {severity_summary.get('parts_with_issues', 0)}", styles['Normal']))
            story.append(Paragraph(f"Worst Severity Level: {severity_summary.get('worst_severity', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Body parts table
            table_data = [["Body Part", "Severity", "Event Count", "Last Updated"]]
            
            for part in body_parts_data.get("parts", [])[:20]:  # Limit to first 20
                table_data.append([
                    part.get("name", "Unknown"),
                    part.get("severity", "N/A"),
                    str(part.get("event_count", 0)),
                    part.get("last_updated", "N/A")[:10] if part.get("last_updated") else "N/A"
                ])
            
            if table_data:
                table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
                    ('GRID', (0, 0), (-1, -1), 1, black)
                ]))
                story.append(table)
        
        # Timeline Section
        if "timeline" in report_data and "error" not in report_data["timeline"]:
            story.append(PageBreak())
            story.append(Paragraph("Medical Timeline", styles['Heading2']))
            
            timeline_data = report_data["timeline"]
            
            # Timeline summary
            story.append(Paragraph(f"Total Events: {timeline_data.get('total_events', 0)}", styles['Normal']))
            
            event_summary = timeline_data.get("event_summary", {})
            recent_count = event_summary.get("recent_count", 0)
            story.append(Paragraph(f"Recent Events (Last 30 days): {recent_count}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Recent events table
            events = timeline_data.get("events", [])[:15]  # Show last 15 events
            if events:
                story.append(Paragraph("Recent Medical Events", styles['Heading3']))
                
                event_table_data = [["Date", "Title", "Type", "Severity"]]
                
                for event in events:
                    timestamp = event.get("timestamp", "")
                    date_str = timestamp[:10] if timestamp else "Unknown"
                    
                    event_table_data.append([
                        date_str,
                        event.get("title", "Untitled")[:30] + ("..." if len(event.get("title", "")) > 30 else ""),
                        event.get("type", "Unknown"),
                        event.get("severity", "N/A")
                    ])
                
                event_table = Table(event_table_data, colWidths=[1*inch, 3*inch, 1*inch, 1*inch])
                event_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
                    ('GRID', (0, 0), (-1, -1), 1, black)
                ]))
                story.append(event_table)
        
        # Footer
        story.append(PageBreak())
        story.append(Paragraph("Report Generated By", styles['Heading3']))
        story.append(Paragraph("MediTwin Health Platform - AI-Powered Medical Data Analysis", styles['Normal']))
        story.append(Paragraph("This report is confidential and intended for medical use only.", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
        
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise Exception(f"PDF generation failed: {e}")
