"""
Aggregator Agent - Synthesizes multiple specialist opinions into unified responses.

This module implements an aggregator agent that combines and synthesizes
multiple specialist medical opinions into a coherent, patient-friendly response.
"""

import json
import asyncio
from typing import List, Dict, Optional, AsyncGenerator, Any
from dataclasses import dataclass
from openai import AsyncOpenAI

from src.config.settings import settings
from src.utils.logging import logger
from src.agents.base_specialist import SpecialistOpinion
from src.prompts import get_agent_prompt

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key)


@dataclass
class AggregatedResponse:
    """Represents an aggregated response from multiple specialists."""
    question: str
    specialist_opinions: List[SpecialistOpinion]
    aggregated_response: str
    confidence_score: float
    primary_recommendations: List[str]
    consensus_areas: List[str]
    conflicting_areas: List[str]
    next_steps: List[str]


class AggregatorAgent:
    """
    Aggregator agent that synthesizes multiple specialist opinions.
    
    Takes opinions from various medical specialists and creates a unified,
    coherent response that addresses the patient's question comprehensively.
    """
    
    def __init__(self):
        """Initialize the aggregator agent."""
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the aggregator system prompt."""
        try:
            return get_agent_prompt("aggregator")
        except Exception as e:
            logger.warning(f"Failed to load aggregator prompt: {e}")
            # Fallback prompt
            return """You are Dr. MediTwin Chief, the Chief Medical Officer coordinating a multidisciplinary medical consultation.

Your role:
- Synthesize multiple specialist answers into one coherent patient-friendly response
- Highlight consensus areas and explain any conflicts clearly
- Assign overall confidence (minimum of inputs unless justified higher)
- Deliver layperson-readable summary avoiding unnecessary jargon

Input: List of specialist JSON responses with {summary, confidence, sources}
Output: Single JSON with {summary, confidence, sources}

Never add facts not present in specialist sources. If insufficient data, state: 'Data insufficient for definitive conclusion.'

5. INTEGRATION: Create coherent, actionable medical advice
6. COMMUNICATION: Present findings in patient-friendly language

KEY RESPONSIBILITIES:
- Combine specialist insights into unified assessment
- Resolve contradictions between specialist opinions
- Identify most critical recommendations for patient safety
- Provide clear next steps and care coordination
- Ensure comprehensive coverage of patient concerns
- Maintain medical accuracy while improving clarity

COMMUNICATION PRINCIPLES:
- Use clear, jargon-free language accessible to patients
- Prioritize most important information first
- Explain medical reasoning in understandable terms
- Address patient's original question directly
- Provide actionable next steps
- Acknowledge uncertainty when present

SYNTHESIS FRAMEWORK:
- Emergency/urgent issues (require immediate attention)
- Primary diagnosis and treatment recommendations
- Secondary conditions and monitoring needs
- Preventive measures and lifestyle modifications
- Follow-up care and specialist referrals
- Patient education and self-management

QUALITY STANDARDS:
- Ensure medical accuracy and evidence-based recommendations
- Maintain internal consistency across all recommendations
- Address all aspects of the original question
- Provide appropriate caveats and limitations
- Emphasize importance of professional medical care
- Include relevant safety considerations

When aggregating specialist opinions:
1. Start with the most urgent or critical findings
2. Synthesize diagnosis and assessment into clear explanation
3. Combine treatment recommendations, noting any specialist-specific nuances
4. Provide unified list of next steps and follow-up care
5. Include relevant patient education and lifestyle advice
6. Address any remaining questions or concerns

Remember: Your goal is to provide the patient with a clear, comprehensive, and actionable medical summary that integrates the best insights from all consulting specialists while maintaining the highest standards of medical care."""
    
    async def aggregate_opinions(
        self,
        question: str,
        specialist_opinions: List[SpecialistOpinion],
        context: Optional[Dict] = None
    ) -> AggregatedResponse:
        """
        Aggregate multiple specialist opinions into a unified response.
        
        Args:
            question: Original patient question
            specialist_opinions: List of specialist opinions to aggregate
            context: Additional context for aggregation
            
        Returns:
            Aggregated response with unified recommendations
        """
        try:
            if not specialist_opinions:
                return AggregatedResponse(
                    question=question,
                    specialist_opinions=[],
                    aggregated_response="No specialist opinions were provided for aggregation.",
                    confidence_score=0.0,
                    primary_recommendations=[],
                    consensus_areas=[],
                    conflicting_areas=[],
                    next_steps=[]
                )
            
            # Prepare the aggregation prompt
            opinions_text = self._format_specialist_opinions(specialist_opinions)
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"""Please aggregate the following specialist opinions for this patient question:

PATIENT QUESTION: {question}

SPECIALIST OPINIONS:
{opinions_text}

Please provide a comprehensive, unified response that:
1. Addresses the patient's question directly
2. Synthesizes the specialist recommendations
3. Identifies areas of consensus and any conflicts
4. Provides clear next steps
5. Uses patient-friendly language

Format your response as a clear, structured medical summary."""
                }
            ]
            
            # Generate aggregated response
            response = await client.chat.completions.create(
                model=settings.openai_model_chat,
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            
            aggregated_text = response.choices[0].message.content
            
            # Analyze the aggregation
            analysis = self._analyze_aggregation(specialist_opinions, aggregated_text)
            
            return AggregatedResponse(
                question=question,
                specialist_opinions=specialist_opinions,
                aggregated_response=aggregated_text,
                confidence_score=analysis["confidence_score"],
                primary_recommendations=analysis["primary_recommendations"],
                consensus_areas=analysis["consensus_areas"],
                conflicting_areas=analysis["conflicting_areas"],
                next_steps=analysis["next_steps"]
            )
            
        except Exception as e:
            logger.error(f"Failed to aggregate specialist opinions: {e}")
            return AggregatedResponse(
                question=question,
                specialist_opinions=specialist_opinions,
                aggregated_response=f"Error aggregating specialist opinions: {str(e)}",
                confidence_score=0.0,
                primary_recommendations=[],
                consensus_areas=[],
                conflicting_areas=[],
                next_steps=[]
            )
    
    async def stream_aggregated_response(
        self,
        question: str,
        specialist_opinions: List[SpecialistOpinion],
        context: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream an aggregated response as it's being generated.
        
        Args:
            question: Original patient question
            specialist_opinions: List of specialist opinions to aggregate
            context: Additional context for aggregation
            
        Yields:
            Chunks of the aggregated response
        """
        try:
            if not specialist_opinions:
                yield {
                    "type": "error",
                    "message": "No specialist opinions provided for aggregation"
                }
                return
            
            # Start aggregation
            yield {
                "type": "aggregation_start",
                "message": "Synthesizing specialist opinions...",
                "specialist_count": len(specialist_opinions)
            }
            
            # Prepare the aggregation prompt
            opinions_text = self._format_specialist_opinions(specialist_opinions)
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"""Please aggregate the following specialist opinions for this patient question:

PATIENT QUESTION: {question}

SPECIALIST OPINIONS:
{opinions_text}

Please provide a comprehensive, unified response."""
                }
            ]
            
            # Stream the aggregated response
            stream = await client.chat.completions.create(
                model=settings.openai_model_chat,
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                stream=True
            )
            
            full_content = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield {
                        "type": "content_chunk",
                        "content": content
                    }
            
            # Complete aggregation
            yield {
                "type": "aggregation_complete",
                "full_response": full_content,
                "specialist_count": len(specialist_opinions)
            }
            
        except Exception as e:
            logger.error(f"Error streaming aggregated response: {e}")
            yield {
                "type": "error",
                "message": f"Error generating aggregated response: {str(e)}"
            }
    
    def _format_specialist_opinions(self, opinions: List[SpecialistOpinion]) -> str:
        """Format specialist opinions for aggregation."""
        formatted_opinions = []
        
        for opinion in opinions:
            opinion_text = f"""
SPECIALIST: {opinion.specialty.upper()}
CONFIDENCE: {opinion.confidence:.1%}

PRIMARY ASSESSMENT:
{opinion.primary_assessment}

RECOMMENDATIONS:
{chr(10).join(f"- {rec}" for rec in opinion.recommendations)}

DIFFERENTIAL DIAGNOSES:
{chr(10).join(f"- {diag}" for diag in opinion.differential_diagnoses)}

REQUESTED TESTS:
{chr(10).join(f"- {test}" for test in opinion.requested_tests)}
"""
            formatted_opinions.append(opinion_text.strip())
        
        return "\n\n" + "="*60 + "\n\n".join(formatted_opinions)
    
    def _analyze_aggregation(
        self,
        specialist_opinions: List[SpecialistOpinion],
        aggregated_text: str
    ) -> Dict[str, Any]:
        """Analyze the aggregation quality and extract key components."""
        
        # Calculate average confidence
        if specialist_opinions:
            avg_confidence = sum(op.confidence for op in specialist_opinions) / len(specialist_opinions)
        else:
            avg_confidence = 0.0
        
        # Extract recommendations (simplified parsing)
        lines = aggregated_text.split('\n')
        primary_recommendations = []
        next_steps = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ["recommend", "suggest", "should"]):
                primary_recommendations.append(line)
            elif any(keyword in line.lower() for keyword in ["next", "follow", "schedule"]):
                next_steps.append(line)
        
        # Identify consensus areas (simplified)
        consensus_areas = []
        all_recommendations = []
        for opinion in specialist_opinions:
            all_recommendations.extend(opinion.recommendations)
        
        # Look for common themes
        common_words = ["medication", "test", "imaging", "follow-up", "monitoring"]
        for word in common_words:
            if sum(1 for rec in all_recommendations if word in rec.lower()) > 1:
                consensus_areas.append(f"Multiple specialists agree on {word}")
        
        return {
            "confidence_score": avg_confidence,
            "primary_recommendations": primary_recommendations[:5],
            "consensus_areas": consensus_areas,
            "conflicting_areas": [],  # Would need more sophisticated analysis
            "next_steps": next_steps[:3]
        }

    async def synthesize_response(
        self,
        user_query: str,
        specialist_responses: List[Dict],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Synthesize specialist responses into a unified response.
        
        Args:
            user_query: Original user question
            specialist_responses: List of specialist response dictionaries
            context: Additional context
            
        Returns:
            Synthesized response dictionary
        """
        try:
            # Convert specialist response dictionaries to SpecialistOpinion objects
            specialist_opinions = []
            for resp in specialist_responses:
                opinion = SpecialistOpinion(
                    specialty=resp.get("specialist_type", "unknown"),
                    confidence=resp.get("confidence", 0.8),
                    primary_assessment=resp.get("response", "")[:500],
                    recommendations=[],
                    differential_diagnoses=[],
                    requested_tests=[],
                    tool_calls=[],
                    reasoning_steps=[]
                )
                specialist_opinions.append(opinion)
            
            # Use the existing aggregation method
            result = await self.aggregate_opinions(user_query, specialist_opinions, context)
            
            return {
                "content": result.aggregated_response,
                "confidence": result.confidence_score,
                "specialist_count": len(specialist_responses),
                "recommendations": result.primary_recommendations,
                "next_steps": result.next_steps
            }
            
        except Exception as e:
            logger.error(f"Failed to synthesize response: {e}")
            return {
                "content": f"Error synthesizing specialist responses: {str(e)}",
                "confidence": 0.0,
                "specialist_count": 0,
                "recommendations": [],
                "next_steps": []
            }

    async def stream_synthesis(
        self,
        user_query: str,
        specialist_responses: List[Dict],
        context: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream synthesis of specialist responses.
        
        Args:
            user_query: Original user question
            specialist_responses: List of specialist response dictionaries
            context: Additional context
            
        Yields:
            Streaming response chunks
        """
        try:
            # Convert specialist response dictionaries to SpecialistOpinion objects
            specialist_opinions = []
            for resp in specialist_responses:
                opinion = SpecialistOpinion(
                    specialty=resp.get("specialist_type", "unknown"),
                    confidence=resp.get("confidence", 0.8),
                    primary_assessment=resp.get("response", "")[:500],
                    recommendations=[],
                    differential_diagnoses=[],
                    requested_tests=[],
                    tool_calls=[],
                    reasoning_steps=[]
                )
                specialist_opinions.append(opinion)
            
            # Use the existing streaming method
            async for chunk in self.stream_aggregated_response(user_query, specialist_opinions, context):
                # Transform to match expected format
                if chunk.get("type") == "content_chunk":
                    yield {
                        "type": "content",
                        "content": chunk["content"]
                    }
                elif chunk.get("type") == "aggregation_start":
                    yield {
                        "type": "metadata",
                        "content": "Synthesizing specialist opinions..."
                    }
                elif chunk.get("type") == "aggregation_complete":
                    yield {
                        "type": "complete",
                        "content": "Synthesis complete",
                        "specialist_count": len(specialist_responses)
                    }
                elif chunk.get("type") == "error":
                    yield {
                        "type": "error",
                        "content": chunk["message"]
                    }
                    
        except Exception as e:
            logger.error(f"Error streaming synthesis: {e}")
            yield {
                "type": "error",
                "content": f"Error generating synthesis: {str(e)}"
            }
    
# Create default instance
aggregator_agent = AggregatorAgent()


async def get_aggregator() -> AggregatorAgent:
    """Get the default aggregator agent instance."""
    return aggregator_agent


# Legacy compatibility functions
async def aggregate(question: str, specialist_outputs: List[str]) -> str:
    """Legacy compatibility function for simple aggregation."""
    try:
        # Convert simple outputs to SpecialistOpinion objects
        opinions = []
        for i, output in enumerate(specialist_outputs):
            opinion = SpecialistOpinion(
                specialty=f"specialist_{i}",
                confidence=0.8,
                primary_assessment=output[:200],
                recommendations=[],
                differential_diagnoses=[],
                requested_tests=[],
                tool_calls=[],
                reasoning_steps=[]
            )
            opinions.append(opinion)
        
        result = await aggregator_agent.aggregate_opinions(question, opinions)
        return result.aggregated_response
        
    except Exception as e:
        logger.error(f"Legacy aggregation failed: {e}")
        return f"Error aggregating responses: {str(e)}"


async def aggregate_stream(question: str, specialist_outputs: List[str]):
    """Legacy compatibility function for streaming aggregation."""
    try:
        # Convert simple outputs to SpecialistOpinion objects
        opinions = []
        for i, output in enumerate(specialist_outputs):
            opinion = SpecialistOpinion(
                specialty=f"specialist_{i}",
                confidence=0.8,
                primary_assessment=output[:200],
                recommendations=[],
                differential_diagnoses=[],
                requested_tests=[],
                tool_calls=[],
                reasoning_steps=[]
            )
            opinions.append(opinion)
        
        async for chunk in aggregator_agent.stream_aggregated_response(question, opinions):
            if chunk.get("type") == "content_chunk":
                yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk['content']}}]})}\n\n"
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Legacy streaming aggregation failed: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
