"""
Health report export functionality for generating PDF reports.
"""

import io
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from src.utils.logging import logger


class HealthReportGenerator:
    """Generates PDF health reports for patients."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for the report."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'], 
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
    
    async def generate_health_report(
        self, 
        patient_id: str, 
        body_parts_data: List[Dict],
        timeline_events: List[Dict],
        patient_profile: Optional[Dict] = None
    ) -> bytes:
        """
        Generate a comprehensive health report PDF.
        
        Args:
            patient_id: Patient identifier
            body_parts_data: Body part severity data
            timeline_events: Timeline of medical events
            patient_profile: Optional patient profile information
        
        Returns:
            PDF bytes
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            # Title
            title = Paragraph("Medical Health Report", self.styles['CustomTitle'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Report metadata
            report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            metadata_text = f"""
            <b>Report Generated:</b> {report_date}<br/>
            <b>Patient ID:</b> {patient_id}<br/>
            <b>Report Type:</b> Comprehensive Health Summary
            """
            story.append(Paragraph(metadata_text, self.styles['BodyText']))
            story.append(Spacer(1, 20))
            
            # Patient Profile Section (if available)
            if patient_profile:
                story.append(Paragraph("Patient Profile", self.styles['SectionHeader']))
                self._add_profile_section(story, patient_profile)
                story.append(Spacer(1, 15))
            
            # Current Health Status Section
            story.append(Paragraph("Current Health Status", self.styles['SectionHeader']))
            self._add_health_status_section(story, body_parts_data)
            story.append(Spacer(1, 15))
            
            # Body Parts Severity Table
            story.append(Paragraph("Body Parts Assessment", self.styles['SectionHeader']))
            self._add_body_parts_table(story, body_parts_data)
            story.append(Spacer(1, 15))
            
            # Timeline Section
            story.append(Paragraph("Recent Medical Events", self.styles['SectionHeader']))
            self._add_timeline_section(story, timeline_events)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate health report")
    
    def _add_profile_section(self, story: List, profile: Dict):
        """Add patient profile information to the report."""
        profile_text = f"""
        <b>Age:</b> {profile.get('age', 'Not specified')}<br/>
        <b>Gender:</b> {profile.get('gender', 'Not specified')}<br/>
        <b>Primary Conditions:</b> {', '.join(profile.get('chronic_conditions', ['None']))}<br/>
        <b>Allergies:</b> {', '.join(profile.get('allergies', ['None']))}<br/>
        """
        story.append(Paragraph(profile_text, self.styles['BodyText']))
    
    def _add_health_status_section(self, story: List, body_parts_data: List[Dict]):
        """Add overall health status summary."""
        # Analyze overall health
        severity_counts = {}
        for part in body_parts_data:
            severity = part.get('severity', 'NA')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Calculate health score (simple algorithm)
        total_parts = len(body_parts_data)
        severity_weights = {'NA': 0, 'normal': 0, 'mild': 1, 'moderate': 2, 'severe': 3, 'critical': 4}
        weighted_score = sum(severity_counts.get(sev, 0) * weight for sev, weight in severity_weights.items())
        max_possible_score = total_parts * 4  # All critical
        
        if max_possible_score > 0:
            health_percentage = max(0, 100 - (weighted_score / max_possible_score * 100))
        else:
            health_percentage = 100
        
        # Determine health category
        if health_percentage >= 90:
            health_category = "Excellent"
            health_color = "green"
        elif health_percentage >= 75:
            health_category = "Good" 
            health_color = "blue"
        elif health_percentage >= 60:
            health_category = "Fair"
            health_color = "orange"
        else:
            health_category = "Needs Attention"
            health_color = "red"
        
        status_text = f"""
        <b>Overall Health Score:</b> {health_percentage:.1f}/100<br/>
        <b>Health Category:</b> <font color="{health_color}">{health_category}</font><br/><br/>
        <b>Severity Breakdown:</b><br/>
        • Normal: {severity_counts.get('normal', 0)} body parts<br/>
        • Mild Issues: {severity_counts.get('mild', 0)} body parts<br/>
        • Moderate Issues: {severity_counts.get('moderate', 0)} body parts<br/>
        • Severe Issues: {severity_counts.get('severe', 0)} body parts<br/>
        • Critical Issues: {severity_counts.get('critical', 0)} body parts<br/>
        """
        story.append(Paragraph(status_text, self.styles['BodyText']))
    
    def _add_body_parts_table(self, story: List, body_parts_data: List[Dict]):
        """Add body parts severity table."""
        # Prepare table data
        table_data = [['Body Part', 'Current Severity', 'Status']]
        
        # Sort by severity (worst first)
        severity_order = {'critical': 0, 'severe': 1, 'moderate': 2, 'mild': 3, 'normal': 4, 'NA': 5}
        sorted_parts = sorted(
            body_parts_data, 
            key=lambda x: severity_order.get(x.get('severity', 'NA'), 5)
        )
        
        for part in sorted_parts:
            severity = part.get('severity', 'NA')
            body_part = part.get('name', part.get('body_part', 'Unknown'))
            
            # Color code severity
            if severity == 'critical':
                severity_display = f'<font color="red">{severity.title()}</font>'
                status = "⚠️ Urgent attention needed"
            elif severity == 'severe':
                severity_display = f'<font color="darkorange">{severity.title()}</font>'
                status = "⚠️ Medical attention recommended"  
            elif severity == 'moderate':
                severity_display = f'<font color="orange">{severity.title()}</font>'
                status = "⚡ Monitor closely"
            elif severity == 'mild':
                severity_display = f'<font color="gold">{severity.title()}</font>'
                status = "👁️ Watch for changes"
            elif severity == 'normal':
                severity_display = f'<font color="green">{severity.title()}</font>'
                status = "✅ No issues detected"
            else:
                severity_display = severity
                status = "❓ No data available"
            
            table_data.append([
                body_part,
                Paragraph(severity_display, self.styles['BodyText']),
                status
            ])
        
        # Create table
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
    
    def _add_timeline_section(self, story: List, timeline_events: List[Dict]):
        """Add recent medical events timeline."""
        if not timeline_events:
            story.append(Paragraph("No recent medical events recorded.", self.styles['BodyText']))
            return
        
        # Sort events by date (most recent first)
        sorted_events = sorted(
            timeline_events, 
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # Take most recent 20 events to fit in PDF
        recent_events = sorted_events[:20]
        
        story.append(Paragraph(f"Showing {len(recent_events)} most recent events:", self.styles['BodyText']))
        story.append(Spacer(1, 10))
        
        for event in recent_events:
            event_date = event.get('timestamp', 'Unknown date')
            event_title = event.get('title', event.get('event_type', 'Medical Event'))
            event_description = event.get('description', 'No description available')
            event_severity = event.get('severity', 'unknown')
            
            # Format the date
            try:
                if 'T' in event_date:
                    dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                else:
                    formatted_date = event_date
            except:
                formatted_date = event_date
            
            event_text = f"""
            <b>{formatted_date}</b> - <b>{event_title}</b><br/>
            {event_description}<br/>
            <i>Severity: {event_severity.title()}</i>
            """
            
            story.append(Paragraph(event_text, self.styles['BodyText']))
            story.append(Spacer(1, 8))
        
        # Add disclaimer
        disclaimer_text = """
        <br/><b>Important:</b> This report is generated based on available data and should not replace 
        professional medical advice. Please consult with your healthcare provider for medical decisions.
        """
        story.append(Paragraph(disclaimer_text, self.styles['BodyText']))


# Global instance
report_generator = HealthReportGenerator()
