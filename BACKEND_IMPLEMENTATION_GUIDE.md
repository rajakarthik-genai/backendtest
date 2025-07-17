# Enhanced Digital Twin Health Dashboard - Backend Implementation Guide

This guide provides step-by-step instructions for implementing the backend FastAPI endpoints to support all the enhanced features of the Digital Twin Health Dashboard.

## Overview of New Features

The enhanced dashboard includes:
1. **Expert Opinion Mode** - Deep research chat powered by multi-agent AI system
2. **Interactive Timeline** - Body region-specific medical event timeline with year/month drill-down
3. **Enhanced Chat System** - Normal and expert mode chat with citation support
4. **Improved UI** - ChatGPT-style sidebar with sources panel

## Required FastAPI Endpoints

### 1. Timeline Endpoint

**Endpoint:** `GET /api/health/timeline`
**Parameters:** `region` (query parameter)

```python
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI()

class TimelineEvent(BaseModel):
    date: str  # ISO format: "2024-07-15"
    summary: str
    severity: str = "normal"  # "normal", "mild", "moderate", "severe"

class TimelineResponse(BaseModel):
    region: str
    events: List[TimelineEvent]

@app.get("/api/health/timeline", response_model=TimelineResponse)
async def get_timeline(region: str = Query(..., description="Body region to get timeline for")):
    """
    Get medical timeline events for a specific body region.
    This should query your Neo4j database for events related to the region.
    """
    # Example Neo4j query (adapt to your schema):
    # MATCH (p:Patient {id: $patient_id})-[:HAS_EVENT]->(e:Event)-[:RELATED_TO]->(r:Region {name: $region})
    # RETURN e.date as date, e.summary as summary, e.severity as severity
    # ORDER BY e.date DESC
    
    try:
        # Query your database here
        events = query_events_by_region(region)  # Your implementation
        
        return TimelineResponse(
            region=region,
            events=events
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve timeline: {str(e)}")

def query_events_by_region(region: str) -> List[TimelineEvent]:
    """
    Query Neo4j or your database for events related to the region.
    This is where you implement your actual database logic.
    """
    # Your database query implementation here
    pass
```

### 2. Expert Opinion Endpoint

**Endpoint:** `POST /api/health/expert_opinion`

```python
class ChatMessage(BaseModel):
    message: str

class Source(BaseModel):
    id: int
    title: str
    url: str

class ExpertOpinionResponse(BaseModel):
    answer: str
    sources: List[Source]
    steps: Optional[str] = None

@app.post("/api/health/expert_opinion", response_model=ExpertOpinionResponse)
async def expert_opinion(query: ChatMessage):
    """
    Process a query using the multi-agent research system.
    This integrates with CrewAI, Neo4j, Milvus, and web search.
    """
    user_query = query.message
    
    try:
        # 1. Initialize your multi-agent system
        result = await run_multi_agent_research(user_query)
        
        if not result:
            raise HTTPException(status_code=500, detail="Research failed")
            
        return ExpertOpinionResponse(
            answer=result["answer"],
            sources=result["sources"],
            steps=result.get("steps", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Expert analysis failed: {str(e)}")

async def run_multi_agent_research(query: str) -> dict:
    """
    Your multi-agent research implementation.
    This should coordinate between:
    - Neo4j knowledge graph agent
    - Milvus vector search agent  
    - Web search agent
    - Analysis and synthesis agent
    """
    # Example implementation structure:
    
    # Agent 1: Query patient context from Neo4j
    patient_context = await neo4j_agent.get_patient_context(query)
    
    # Agent 2: Search similar cases in Milvus
    similar_cases = await milvus_agent.search_similar_cases(query, patient_context)
    
    # Agent 3: Web search for latest research
    web_results = await web_search_agent.search_medical_literature(query)
    
    # Agent 4: Synthesize findings
    analysis = await synthesis_agent.analyze_and_synthesize(
        query, patient_context, similar_cases, web_results
    )
    
    return {
        "answer": analysis["synthesized_answer"],
        "sources": analysis["sources"],
        "steps": analysis["research_process"]
    }
```

### 3. Regular Chat Endpoint

**Endpoint:** `POST /api/health/chat`

```python
class ChatResponse(BaseModel):
    answer: str

@app.post("/api/health/chat", response_model=ChatResponse)
async def health_chat(query: ChatMessage):
    """
    Handle regular chat queries (non-expert mode).
    This can use a simpler AI model or rule-based responses.
    """
    user_query = query.message
    
    try:
        # Use a lighter AI model for basic health questions
        response = await basic_health_assistant(user_query)
        
        return ChatResponse(answer=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

async def basic_health_assistant(query: str) -> str:
    """
    Basic health assistant for non-expert queries.
    Can use OpenAI GPT, local model, or rule-based responses.
    """
    # Your implementation here - could be:
    # - OpenAI API call with health context
    # - Local LLM inference
    # - Rule-based response system
    pass
```

### 4. Enhanced Region and History Endpoints

Update existing endpoints to support the new timeline features:

```python
# Update existing region endpoint to include timeline summary
@app.get("/api/health/region/{region}")
async def get_region_data(region: str):
    """Enhanced region data with timeline summary."""
    # Your existing implementation +
    timeline_summary = await get_region_timeline_summary(region)
    
    return {
        "region": region,
        "status": "...",  # Your existing data
        "timeline_summary": timeline_summary,
        # ... other existing fields
    }

async def get_region_timeline_summary(region: str) -> dict:
    """Get a summary of recent events for the region."""
    recent_events = await query_recent_events(region, limit=5)
    return {
        "recent_events": recent_events,
        "total_events": len(recent_events),
        "last_update": recent_events[0]["date"] if recent_events else None
    }
```

## Database Schema Recommendations

### Neo4j Schema for Timeline Data

```cypher
// Patient node
(:Patient {id: "patient123", name: "Dr. Ericsson"})

// Body region nodes
(:Region {name: "heart", display_name: "Cardiovascular System"})
(:Region {name: "lungs", display_name: "Respiratory System"})
(:Region {name: "liver", display_name: "Liver & Hepatic System"})
// ... other regions

// Medical event nodes
(:Event {
  id: "event_001",
  date: "2024-07-15",
  summary: "Routine cardiovascular checkup - excellent results",
  severity: "normal",
  type: "checkup",
  created_at: datetime()
})

// Relationships
(:Patient)-[:HAS_EVENT]->(:Event)
(:Event)-[:RELATED_TO]->(:Region)
(:Event)-[:DOCUMENTED_IN]->(:Document)
```

### Example Cypher Queries

```cypher
// Get timeline events for a region
MATCH (p:Patient {id: $patient_id})-[:HAS_EVENT]->(e:Event)-[:RELATED_TO]->(r:Region {name: $region})
RETURN e.date as date, e.summary as summary, e.severity as severity
ORDER BY e.date DESC

// Get events by year
MATCH (p:Patient {id: $patient_id})-[:HAS_EVENT]->(e:Event)
WHERE e.date STARTS WITH $year
RETURN e
ORDER BY e.date DESC

// Get recent events for dashboard summary
MATCH (p:Patient {id: $patient_id})-[:HAS_EVENT]->(e:Event)
WHERE e.date >= $start_date
RETURN e, [(e)-[:RELATED_TO]->(r:Region) | r.name] as regions
ORDER BY e.date DESC
LIMIT 10
```

## Milvus Integration for Expert Mode

```python
from pymilvus import connections, Collection

class MilvusSearchAgent:
    def __init__(self):
        connections.connect("default", host="localhost", port="19530")
        self.collection = Collection("medical_cases")
    
    async def search_similar_cases(self, query: str, patient_context: dict):
        """Search for similar medical cases using vector similarity."""
        # Convert query to embedding
        query_embedding = await self.get_embedding(query)
        
        # Search similar cases
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=5
        )
        
        return [self.format_case(hit) for hit in results[0]]
    
    async def get_embedding(self, text: str):
        """Convert text to embedding vector."""
        # Use your embedding model (OpenAI, sentence-transformers, etc.)
        pass
    
    def format_case(self, hit):
        """Format search result for agent consumption."""
        return {
            "case_id": hit.id,
            "similarity": hit.score,
            "summary": hit.entity.get("summary"),
            "outcome": hit.entity.get("outcome")
        }
```

## CrewAI Multi-Agent Setup

```python
from crewai import Agent, Task, Crew

class MedicalResearchCrew:
    def __init__(self):
        self.setup_agents()
    
    def setup_agents(self):
        # Neo4j Knowledge Agent
        self.knowledge_agent = Agent(
            role='Medical Knowledge Specialist',
            goal='Extract relevant patient history and medical context',
            backstory='Expert in medical databases and patient history analysis',
            tools=[neo4j_query_tool]
        )
        
        # Research Agent
        self.research_agent = Agent(
            role='Medical Research Specialist',
            goal='Find latest medical research and clinical guidelines',
            backstory='Expert in medical literature and evidence-based medicine',
            tools=[web_search_tool, pubmed_tool]
        )
        
        # Analysis Agent
        self.analysis_agent = Agent(
            role='Clinical Analysis Expert',
            goal='Synthesize findings into actionable medical insights',
            backstory='Senior physician with expertise in differential diagnosis',
            tools=[analysis_tool]
        )
    
    async def research_query(self, query: str) -> dict:
        """Execute multi-agent research for a medical query."""
        
        # Task 1: Get patient context
        context_task = Task(
            description=f"Extract relevant patient history for: {query}",
            agent=self.knowledge_agent
        )
        
        # Task 2: Research latest information
        research_task = Task(
            description=f"Find latest medical research on: {query}",
            agent=self.research_agent
        )
        
        # Task 3: Synthesize findings
        analysis_task = Task(
            description="Synthesize patient context and research into comprehensive answer",
            agent=self.analysis_agent
        )
        
        # Execute crew
        crew = Crew(
            agents=[self.knowledge_agent, self.research_agent, self.analysis_agent],
            tasks=[context_task, research_task, analysis_task]
        )
        
        result = await crew.kickoff()
        return self.format_result(result)
```

## Frontend Integration Notes

The frontend expects these response formats:

1. **Timeline Response:**
```json
{
  "region": "heart",
  "events": [
    {
      "date": "2024-07-15",
      "summary": "Routine checkup completed",
      "severity": "normal"
    }
  ]
}
```

2. **Expert Opinion Response:**
```json
{
  "answer": "Based on analysis... [1][2]",
  "sources": [
    {
      "id": 1,
      "title": "Medical Journal Article",
      "url": "https://example.com"
    }
  ],
  "steps": "Research process description"
}
```

## CORS Configuration

Don't forget to enable CORS for your frontend:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Testing the Implementation

1. Start your FastAPI server: `uvicorn main:app --reload --port 8000`
2. Start the frontend: `./start-frontend.sh`
3. Test timeline functionality by clicking body regions
4. Test expert opinion mode with the toggle enabled
5. Verify sources panel appears with expert responses

This implementation provides a complete backend to support all the enhanced dashboard features with proper multi-agent AI integration.
