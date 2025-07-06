"""
Base Specialist Agent - Factory for creating specialist medical agents.

This module provides a base class and factory for creating specialist agents that can:
• Reason step-by-step with domain-specific prompts
• Call domain-agnostic tools (web search, vector search, graph query, document DB)
• Return structured medical opinions
• Support async operation with streaming responses
"""

from __future__ import annotations

import json
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator, Any
from dataclasses import dataclass
from enum import Enum

from src.config.settings import settings
from src.tools import web_search, knowledge_graph, document_db, get_vector_store
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph
from src.utils.logging import logger
from openai import AsyncOpenAI

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key)


class SpecialtyType(Enum):
    """Medical specialty types."""
    GENERAL = "general"
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    ORTHOPEDICS = "orthopedics"


@dataclass
class ToolCall:
    """Represents a tool call made by a specialist."""
    name: str
    arguments: Dict[str, Any]
    result: str
    execution_time: float


@dataclass
class SpecialistOpinion:
    """Structured specialist opinion."""
    specialty: str
    confidence: float
    primary_assessment: str
    recommendations: List[str]
    differential_diagnoses: List[str]
    requested_tests: List[str]
    tool_calls: List[ToolCall]
    reasoning_steps: List[str]


class BaseSpecialist(ABC):
    """
    Base class for all medical specialist agents.
    
    Provides common functionality for tool usage, reasoning,
    and structured opinion generation.
    """
    
    def __init__(self, specialty: SpecialtyType, system_prompt: str):
        """
        Initialize the specialist.
        
        Args:
            specialty: The medical specialty type
            system_prompt: System prompt defining the specialist's role
        """
        self.specialty = specialty
        self.system_prompt = system_prompt
        self.tools_schema = self._get_tools_schema()
        
    def _get_tools_schema(self) -> List[Dict]:
        """Get the OpenAI function calling schema for available tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for current medical guidance and research.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Medical search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_vector_db",
                    "description": "Semantic similarity search in the medical knowledge vector database.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query for semantic search"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_knowledge_graph",
                    "description": "Query the patient's medical knowledge graph for related conditions and events.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query for the knowledge graph"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_patient_records",
                    "description": "Retrieve specific patient medical records by type.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "record_type": {
                                "type": "string",
                                "description": "Type of records to retrieve (labs, imaging, medications, etc.)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of records to retrieve",
                                "default": 10
                            }
                        },
                        "required": ["record_type"]
                    }
                }
            }
        ]
    
    async def _execute_tool(self, user_id: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool call and return the result.
        
        Args:
            user_id: User identifier for context
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result as string
        """
        try:
            if tool_name == "search_web":
                return await self._web_search(arguments["query"])
            
            elif tool_name == "query_vector_db":
                return await self._vector_search(arguments.get("query", ""), user_id)
            
            elif tool_name == "query_knowledge_graph":
                return await self._knowledge_graph_query(arguments.get("query", ""), user_id)
            
            elif tool_name == "get_patient_records":
                mongo_client = await get_mongo()
                records = await mongo_client.get_medical_records(
                    user_id,
                    record_type=arguments["record_type"],
                    limit=arguments.get("limit", 10)
                )
                return json.dumps(records)
            
            else:
                return f"Tool '{tool_name}' is not available."
                
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return f"Tool execution failed: {str(e)}"
    
    async def get_opinion(
        self,
        user_id: str,
        question: str,
        context: Optional[Dict] = None
    ) -> SpecialistOpinion:
        """
        Get a structured medical opinion from the specialist.
        
        Args:
            user_id: User identifier
            question: Medical question or case description
            context: Additional context (medical history, etc.)
            
        Returns:
            Structured specialist opinion
        """
        messages = self._prepare_messages(question, context)
        tool_calls = []
        reasoning_steps = []
        
        try:
            # Initial reasoning phase
            response = await client.chat.completions.create(
                model=settings.openai_model_chat,
                messages=messages,
                tools=self.tools_schema,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=2000
            )
            
            message = response.choices[0].message
            
            # Handle tool calls
            while message.tool_calls:
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [tc.model_dump() for tc in message.tool_calls]
                })
                
                # Execute each tool call
                for tool_call in message.tool_calls:
                    start_time = time.time()
                    
                    result = await self._execute_tool(
                        user_id,
                        tool_call.function.name,
                        json.loads(tool_call.function.arguments)
                    )
                    
                    execution_time = time.time() - start_time
                    
                    # Store tool call for tracking
                    tool_calls.append(ToolCall(
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments),
                        result=result,
                        execution_time=execution_time
                    ))
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                
                # Get next response with tool results
                response = await client.chat.completions.create(
                    model=settings.openai_model_chat,
                    messages=messages,
                    tools=self.tools_schema,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=2000
                )
                
                message = response.choices[0].message
            
            # Generate structured opinion
            final_content = message.content or ""
            
            # Parse the response to extract structured components
            opinion = self._parse_opinion(final_content, tool_calls)
            
            logger.info(f"{self.specialty.value} specialist provided opinion for user {user_id}")
            
            return opinion
            
        except Exception as e:
            logger.error(f"Failed to generate {self.specialty.value} opinion: {e}")
            # Return basic opinion with error information
            return SpecialistOpinion(
                specialty=self.specialty.value,
                confidence=0.0,
                primary_assessment=f"Unable to provide assessment due to error: {str(e)}",
                recommendations=[],
                differential_diagnoses=[],
                requested_tests=[],
                tool_calls=tool_calls,
                reasoning_steps=[]
            )
    
    async def stream_opinion(
        self,
        user_id: str,
        question: str,
        context: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a medical opinion as it's being generated.
        
        Args:
            user_id: User identifier
            question: Medical question or case description
            context: Additional context
            
        Yields:
            Chunks of the opinion as it's generated
        """
        messages = self._prepare_messages(question, context)
        
        try:
            # Stream initial reasoning
            yield {
                "type": "specialist_start",
                "specialty": self.specialty.value,
                "message": f"Consulting {self.specialty.value} specialist..."
            }
            
            stream = await client.chat.completions.create(
                model=settings.openai_model_chat,
                messages=messages,
                tools=self.tools_schema,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=2000,
                stream=True
            )
            
            current_content = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    current_content += content
                    yield {
                        "type": "content_chunk",
                        "specialty": self.specialty.value,
                        "content": content
                    }
            
            # Handle any tool calls after streaming
            if chunk.choices[0].delta.tool_calls:
                yield {
                    "type": "tool_execution_start",
                    "specialty": self.specialty.value,
                    "message": "Consulting additional medical resources..."
                }
                
                # Execute tools and continue (simplified for streaming)
                # In a full implementation, you'd handle tool calls here
            
            yield {
                "type": "specialist_complete",
                "specialty": self.specialty.value,
                "content": current_content
            }
            
        except Exception as e:
            logger.error(f"Error streaming {self.specialty.value} opinion: {e}")
            yield {
                "type": "error",
                "specialty": self.specialty.value,
                "message": f"Error generating opinion: {str(e)}"
            }
    
    def _prepare_messages(self, question: str, context: Optional[Dict] = None) -> List[Dict]:
        """Prepare the conversation messages for the LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        if context:
            context_str = self._format_context(context)
            if context_str:
                messages.append({
                    "role": "system",
                    "content": f"Patient Context:\n{context_str}"
                })
        
        messages.append({
            "role": "user",
            "content": question
        })
        
        return messages
    
    def _format_context(self, context: Dict) -> str:
        """Format context information for the LLM."""
        context_parts = []
        
        if "medical_history" in context:
            history = context["medical_history"][:5]  # Limit context size
            if history:
                context_parts.append("Recent Medical History:")
                for record in history:
                    context_parts.append(f"- {record.get('title', record.get('description', 'Medical event'))}")
        
        if "knowledge_graph" in context:
            kg_data = context["knowledge_graph"]
            if kg_data:
                context_parts.append("Related Medical Information:")
                context_parts.append(str(kg_data)[:500])  # Truncate if too long
        
        return "\n".join(context_parts)
    
    def _parse_opinion(self, content: str, tool_calls: List[ToolCall]) -> SpecialistOpinion:
        """
        Parse the LLM response into a structured opinion.
        
        This is a simplified parser - in production, you might use
        structured output or more sophisticated parsing.
        """
        lines = content.split('\n')
        
        # Extract key components (simplified parsing)
        primary_assessment = content[:200] + "..." if len(content) > 200 else content
        
        # Look for recommendations, diagnoses, etc. in the text
        recommendations = []
        differential_diagnoses = []
        requested_tests = []
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ["recommend", "suggest", "advise"]):
                recommendations.append(line.strip())
            elif any(keyword in line_lower for keyword in ["diagnosis", "consider", "possible"]):
                differential_diagnoses.append(line.strip())
            elif any(keyword in line_lower for keyword in ["test", "exam", "scan", "lab"]):
                requested_tests.append(line.strip())
        
        # Estimate confidence based on tool usage and content quality
        confidence = min(0.9, 0.5 + len(tool_calls) * 0.1 + len(content) / 1000)
        
        return SpecialistOpinion(
            specialty=self.specialty.value,
            confidence=confidence,
            primary_assessment=primary_assessment,
            recommendations=recommendations[:5],  # Limit to top 5
            differential_diagnoses=differential_diagnoses[:3],
            requested_tests=requested_tests[:5],
            tool_calls=tool_calls,
            reasoning_steps=[]  # Could be extracted from content
        )
    
    @abstractmethod
    def get_specialty_prompt(self) -> str:
        """Get the specialty-specific system prompt."""
        pass

    async def _web_search(self, query: str) -> str:
        """Perform web search using the web search tool."""
        try:
            from src.tools.web_search import search
            # Run the search in a thread since it might be blocking
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, search, query)
            return result
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"Web search unavailable: {str(e)}"
    
    async def _vector_search(self, query: str, user_id: str) -> str:
        """Search vector database for similar content."""
        try:
            milvus_client = get_vector_store()
            results = milvus_client.search_similar_documents(
                user_id=user_id,
                query_text=query,
                limit=5,
                score_threshold=0.7
            )
            
            if not results:
                return "No similar documents found"
            
            # Format results for context
            snippets = []
            for result in results:
                content = result.get("content", "")[:200]  # Truncate for context
                score = result.get("similarity_score", 0)
                snippets.append(f"Content: {content}... (score: {score:.2f})")
            
            return "; ".join(snippets)
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return f"Vector search unavailable: {str(e)}"
    
    async def _knowledge_graph_query(self, query: str, user_id: str) -> str:
        """Query the knowledge graph for patient information."""
        try:
            graph_db = get_graph()
            
            # Ensure user is initialized
            graph_db.ensure_user_initialized(user_id)
            
            # Get body part severities
            severities = graph_db.get_body_part_severities(user_id)
            
            # Get recent events for context
            timeline = graph_db.get_patient_timeline(user_id, limit=10)
            
            # Build context response
            context = {
                "body_part_severities": severities,
                "recent_events": timeline,
                "query_processed": True
            }
            
            return json.dumps(context)
            
        except Exception as e:
            logger.error(f"Knowledge graph query failed: {e}")
            return f"Knowledge graph unavailable: {str(e)}"
    
    async def _document_search(self, query: str, user_id: str) -> str:
        """Search patient documents and records."""
        try:
            mongo_client = await get_mongo()
            # Search for relevant documents/records
            records = await mongo_client.get_medical_records(user_id)
            if records:
                return json.dumps({"found_records": len(records), "summary": "Medical records available"})
            else:
                return json.dumps({"found_records": 0, "summary": "No medical records found"})
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return f"Document search unavailable: {str(e)}"

def create_specialist(specialty: SpecialtyType, custom_prompt: Optional[str] = None) -> BaseSpecialist:
    """
    Factory function to create a specialist agent.
    
    Args:
        specialty: The medical specialty type
        custom_prompt: Optional custom system prompt
        
    Returns:
        Configured specialist agent
    """
    from src.agents.general_physician_agent import GeneralPhysicianAgent
    from src.agents.cardiologist_agent import CardiologistAgent
    from src.agents.neurologist_agent import NeurologistAgent
    from src.agents.orthopedist_agent import OrthopedistAgent
    
    specialist_classes = {
        SpecialtyType.GENERAL: GeneralPhysicianAgent,
        SpecialtyType.CARDIOLOGY: CardiologistAgent,
        SpecialtyType.NEUROLOGY: NeurologistAgent,
        SpecialtyType.ORTHOPEDICS: OrthopedistAgent,
    }
    
    specialist_class = specialist_classes.get(specialty)
    if not specialist_class:
        raise ValueError(f"Unknown specialty: {specialty}")
    
    return specialist_class(custom_prompt)
