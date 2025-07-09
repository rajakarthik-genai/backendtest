# Dependencies: none (uses MongoDB from mongo_db.py)
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from openai import AsyncOpenAI
from src.config.settings import settings
from src.utils.logging import logger

client = AsyncOpenAI(api_key=settings.openai_api_key)

class TimelineBuilder:
    """
    Provides methods to query a patient's timeline of medical events and analyze trends.
    Utilizes MongoDB for data retrieval.
    """
    def __init__(self, mongo_client):
        """
        Initialize with an instance of MongoDB for data storage/retrieval.
        """
        self.mongo = mongo_client
    
    def get_timeline(self, patient_id: str, start_date=None, end_date=None):
        """
        Retrieve the patient's timeline of all medical records (events) optionally within a date range.
        Returns a list of records sorted chronologically.
        """
        records = self.mongo.query_timeline(patient_id, start_date=start_date, end_date=end_date)
        return records
    
    def get_history(self, patient_id: str, metric_name: str):
        """
        Retrieve the historical records for a specific metric (e.g., a particular test or condition) for the patient.
        Returns a list of records sorted by timestamp.
        """
        records = self.mongo.get_records_by_metric(patient_id, metric_name)
        return records
    
    def identify_trend(self, patient_id: str, metric_name: str):
        """
        Analyze the trend of a numeric metric across the patient's visits.
        Returns a description of the trend (increasing, decreasing, stable, fluctuating) or a message if data insufficient.
        """
        records = self.mongo.get_records_by_metric(patient_id, metric_name)
        # Extract numeric values in chronological order
        values = []
        for rec in records:
            val = rec.get("value")
            if isinstance(val, (int, float)):
                values.append(float(val))
            elif isinstance(val, bool):
                # Convert boolean to int (True=1, False=0) if present
                values.append(1.0 if val else 0.0)
        if len(values) < 2:
            return "No trend (insufficient data points)"
        first, last = values[0], values[-1]
        # Check monotonicity
        increasing = all(values[i] <= values[i+1] for i in range(len(values)-1))
        decreasing = all(values[i] >= values[i+1] for i in range(len(values)-1))
        if increasing and not decreasing:
            return "Increasing trend"
        if decreasing and not increasing:
            return "Decreasing trend"
        # If values are all equal
        if all(abs(v - values[0]) < 1e-9 for v in values):
            return "Stable trend (no change)"
        # Otherwise, fluctuating
        if last > first:
            return "Fluctuating trend (overall increase)"
        elif last < first:
            return "Fluctuating trend (overall decrease)"
        else:
            return "Fluctuating trend (no net change)"
    
    async def generate_timeline_summary(
        self,
        patient_id: str,
        body_part: Optional[str] = None,
        time_period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Generate an LLM-powered timeline summary with structured event analysis.
        
        Args:
            patient_id: Patient identifier
            body_part: Optional body part filter
            time_period_days: Number of days to look back (default 90)
            
        Returns:
            Structured timeline summary with events, trends, and insights
        """
        try:
            # Get events from the specified time period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=time_period_days)
            
            records = self.get_timeline(patient_id, start_date, end_date)
            
            if not records:
                return {
                    "summary": "No medical events found in the specified time period.",
                    "event_count": 0,
                    "body_parts_affected": [],
                    "severity_distribution": {},
                    "key_insights": []
                }
            
            # Filter by body part if specified
            if body_part:
                records = [r for r in records if r.get('body_part', '').lower() == body_part.lower()]
            
            # Prepare timeline data for LLM analysis
            timeline_events = []
            for record in records[-20:]:  # Limit to most recent 20 events
                event_summary = {
                    "date": record.get('timestamp', record.get('date', 'Unknown')),
                    "title": record.get('title', record.get('description', 'Medical Event')),
                    "body_part": record.get('body_part', 'General'),
                    "severity": record.get('severity', 'Unknown'),
                    "type": record.get('event_type', 'general'),
                    "description": record.get('description', '')[:200]  # Truncate long descriptions
                }
                timeline_events.append(event_summary)
            
            # Call LLM to analyze timeline and generate structured summary
            summary_data = await self._generate_llm_timeline_analysis(timeline_events, body_part)
            
            # Add statistical data
            body_parts_affected = list(set(r.get('body_part', 'General') for r in records if r.get('body_part')))
            severity_counts = {}
            for record in records:
                severity = record.get('severity', 'Unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            return {
                "summary": summary_data.get("narrative_summary", "Timeline analysis completed."),
                "event_count": len(records),
                "body_parts_affected": body_parts_affected,
                "severity_distribution": severity_counts,
                "key_insights": summary_data.get("key_insights", []),
                "treatment_patterns": summary_data.get("treatment_patterns", []),
                "progression_analysis": summary_data.get("progression_analysis", ""),
                "recommendations": summary_data.get("recommendations", []),
                "time_period": f"{time_period_days} days",
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate timeline summary: {e}")
            return {
                "summary": "Timeline analysis failed due to an error.",
                "event_count": 0,
                "body_parts_affected": [],
                "severity_distribution": {},
                "key_insights": [],
                "error": str(e)
            }
    
    async def _generate_llm_timeline_analysis(
        self,
        timeline_events: List[Dict[str, Any]],
        body_part_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate LLM analysis of timeline events."""
        try:
            # Create analysis schema
            analysis_schema = {
                "type": "object",
                "properties": {
                    "narrative_summary": {
                        "type": "string",
                        "description": "A concise narrative summary of the patient's medical timeline"
                    },
                    "key_insights": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Key medical insights derived from the timeline"
                    },
                    "treatment_patterns": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Observed treatment patterns or responses"
                    },
                    "progression_analysis": {
                        "type": "string",
                        "description": "Analysis of condition progression over time"
                    },
                    "recommendations": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Medical recommendations based on timeline analysis"
                    }
                },
                "required": ["narrative_summary", "key_insights"]
            }
            
            # Create system prompt
            system_prompt = """You are a medical timeline analyst. Analyze the provided medical events and generate insights about the patient's health journey.

INSTRUCTIONS:
1. Provide a clear narrative summary of the medical timeline
2. Identify key patterns, trends, or concerning developments
3. Note any treatment responses or medication effects
4. Analyze disease progression or improvement over time
5. Suggest relevant medical recommendations based on the timeline
6. Be objective and base conclusions only on the provided data
7. Use medical terminology appropriately but keep explanations clear

Focus on:
- Symptom progression or resolution
- Treatment effectiveness
- Severity changes over time
- Interconnections between different medical events
- Risk factors or warning signs"""
            
            body_part_context = f"\n\nFocus specifically on events related to: {body_part_filter}" if body_part_filter else ""
            
            user_prompt = f"""Analyze this medical timeline:{body_part_context}

Timeline Events:
{json.dumps(timeline_events, indent=2)}

Provide a structured analysis following the specified schema."""
            
            # Call OpenAI with structured output
            response = await client.chat.completions.create(
                model=settings.openai_model_chat,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "timeline_analysis",
                        "schema": analysis_schema,
                        "strict": True
                    }
                },
                temperature=0.2,
                max_tokens=1500
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Generated timeline analysis with {len(result.get('key_insights', []))} insights")
            return result
            
        except Exception as e:
            logger.error(f"LLM timeline analysis failed: {e}")
            return {
                "narrative_summary": "Timeline analysis could not be completed.",
                "key_insights": ["Analysis failed due to processing error"],
                "treatment_patterns": [],
                "progression_analysis": "Unable to analyze progression",
                "recommendations": []
            }
