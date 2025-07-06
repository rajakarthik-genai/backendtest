# 🔍 MediTwin Body Parts Data Generation - Complete Technical Analysis

## 📊 Data Flow Overview

The body parts severity data in MediTwin is generated through a multi-stage process involving **rule-based algorithms**, **keyword extraction**, and **Neo4j graph calculations**. Here's the complete technical breakdown:

## 🏗️ Data Generation Architecture

### 1. **Initial Data Sources**
```
Document Upload → Text Extraction → Entity Recognition → Neo4j Storage → Severity Calculation
```

### 2. **Key Components Involved**

#### A. **Document Ingestion Agent** (`src/agents/ingestion_agent.py`)
- **Role**: Processes uploaded medical documents
- **Method**: Keyword-based extraction (NOT LLM-based)
- **Location**: Lines 160-200

```python
async def _extract_medical_entities(self, text: str) -> List[Dict[str, Any]]:
    """Extract medical entities using KEYWORD MATCHING"""
    medical_keywords = {
        "conditions": ["diabetes", "hypertension", "asthma", "pneumonia", "covid", "cancer"],
        "medications": ["metformin", "lisinopril", "albuterol", "aspirin", "insulin"],
        "body_parts": ["heart", "lung", "liver", "kidney", "brain", "arm", "leg"],
        "symptoms": ["pain", "fever", "cough", "fatigue", "nausea", "headache"]
    }
    
    # Simple string matching - NO LLM INVOLVED HERE
    for category, keywords in medical_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                entities.append({
                    "type": category,
                    "text": keyword,
                    "confidence": 0.8
                })
```

#### B. **Neo4j Severity Calculator** (`src/db/neo4j_db.py`)
- **Role**: Calculates body part severities using **MATHEMATICAL ALGORITHMS**
- **Method**: Rule-based scoring with weighted calculations
- **Location**: Lines 625-720

```python
def calculate_severity_from_events(self, user_id: str, body_part: str) -> str:
    """
    RULE-BASED SEVERITY CALCULATION (NO LLM)
    Uses mathematical scoring with event weights
    """
    # Severity weight mapping
    severity_weights = {
        "critical": 10,
        "severe": 7,
        "moderate": 4,
        "mild": 2,
        "normal": 1
    }
    
    # Calculate weighted scores
    for event in events:
        severity = event.get("event_severity", "mild")
        confidence = event.get("confidence", 0.8)
        event_type = event.get("event_type", "general")
        
        # Mathematical weighting formula
        weight = severity_weights.get(severity, 2)
        confidence_multiplier = max(0.5, confidence)
        
        # Event type multipliers
        type_multiplier = 1.0
        if event_type in ["surgery", "emergency", "hospitalization"]:
            type_multiplier = 1.5
        elif event_type in ["medication", "treatment"]:
            type_multiplier = 1.2
        
        weighted_score = weight * confidence_multiplier * type_multiplier
        total_score += weighted_score
    
    # Final severity determination (ALGORITHMIC)
    average_score = total_score / total_events
    
    if critical_count > 0 or average_score >= 8:
        return "critical"
    elif severe_count > 0 or average_score >= 6:
        return "severe"
    elif moderate_count > 1 or average_score >= 4:
        return "moderate"
    elif total_events > 3 or average_score >= 2:
        return "mild"
    else:
        return "normal"
```

## 🤖 LLM Agent Involvement

### **Where LLMs ARE Used:**

#### 1. **Entity Extraction Prompt** (`src/prompts/entities.json`)
```json
{
    "system": "You are a clinical NLP model. Extract labs, vitals, medications, conditions (explicit or inferred), injuries, organs and treatments from the document. Use JSON with keys exactly: lab_results[], vitals[], medications[], conditions[], injuries[], organs[], treatments[]. For labs include name,value,unit,flag,date. Infer condition names when abnormal results strongly suggest one. Return only JSON. No extra keys."
}
```

#### 2. **Specialist Agent Prompts** (For Expert Opinions)

**Cardiologist Agent Prompt:**
```json
{
    "agent": "Cardiologist Agent",
    "role": "Heart & circulatory system expert.",
    "goals": [
        "Interpret cardiovascular symptoms and patient heart-related data accurately.",
        "Explain heart findings in clear, patient-friendly language.",
        "Request extra tests only when truly necessary."
    ],
    "step_by_step_reasoning": [
        "1️⃣ Read patient's query and any provided vitals/history.",
        "2️⃣ Decide if current knowledge suffices. If not, pick tool:",
        "   • For guideline thresholds → vector_store",
        "   • For up-to-date trial info → web_search", 
        "   • For patient lab numbers → document_db",
        "   • For pathophysiology links → knowledge_graph",
        "3️⃣ If data contradictory, state uncertainty not speculation.",
        "4️⃣ Draft a summary focused solely on cardiac aspects.",
        "5️⃣ Rate confidence (1-10).",
        "6️⃣ Output JSON {summary, confidence, sources}."
    ],
    "output_schema": "summary:str, confidence:int, sources:list[str]"
}
```

## 📈 Complete Data Generation Process

### **Phase 1: Document Processing**
```
User Uploads Document → PDF/Image Text Extraction → Keyword Matching → 
Extract Medical Entities → Store in MongoDB → Create Neo4j Events
```

### **Phase 2: Neo4j Graph Building**
```python
# Auto-triggered in create_medical_event()
for entity in extracted_entities:
    if entity["type"] in ["conditions", "symptoms"]:
        event_data = {
            "title": entity["text"],
            "description": f"Mentioned in document {document_id}",
            "event_type": "condition",
            "timestamp": datetime.utcnow(),
            "severity": "medium"  # Initial severity
        }
        neo4j_client.create_medical_event(user_id, event_data)
```

### **Phase 3: Severity Calculation**
```python
# Auto-triggered after event creation
for body_part in affected_body_parts:
    new_severity = calculate_severity_from_events(user_id, body_part)
    update_body_part_severity(user_id, body_part, new_severity)
```

### **Phase 4: API Data Retrieval**
```python
# GET /anatomy/body-parts
def get_body_parts_severities():
    # Neo4j Cypher Query
    query = """
    MATCH (b:BodyPart)
    WHERE b.name IN $body_parts
    OPTIONAL MATCH (p:Patient {patient_id: $patient_id})-[r:HAS_BODY_PART]->(b)
    RETURN b.name as body_part, 
           coalesce(r.severity, 'NA') as severity,
           coalesce(r.event_count, 0) as event_count
    ORDER BY b.name
    """
    
    # Returns: {"body_parts": [{"name": "Heart", "severity": "mild"}, ...]}
```

## 🔧 Neo4j Schema & Queries

### **Graph Structure:**
```cypher
// Patient with body part relationships
(Patient {patient_id: hashed_user_id})
  -[:HAS_BODY_PART {severity: "mild", event_count: 3, last_updated: timestamp}]→
(BodyPart {name: "Heart"})

// Medical events affecting body parts  
(Patient)-[:HAS_EVENT]→(Event {title, severity, timestamp})
  -[:AFFECTS]→(BodyPart)
```

### **Key Queries Used:**

#### 1. **Get All Body Part Severities**
```cypher
MATCH (b:BodyPart)
WHERE b.name IN $body_parts
OPTIONAL MATCH (p:Patient {patient_id: $patient_id})-[r:HAS_BODY_PART]->(b)
RETURN b.name as body_part, 
       coalesce(r.severity, 'NA') as severity
ORDER BY b.name
```

#### 2. **Get Body Part Event History**
```cypher
MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)-[:AFFECTS]->(b:BodyPart {name: $body_part})
RETURN e.event_id, e.title, e.description, e.event_type, e.timestamp, e.severity
ORDER BY e.timestamp DESC
```

#### 3. **Calculate Severity from Recent Events**
```cypher
MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)-[:AFFECTS]->(b:BodyPart {name: $body_part})
WHERE e.timestamp >= datetime() - duration({days: 90})
RETURN e.severity, e.event_type, e.confidence, count(e) as event_count
ORDER BY e.timestamp DESC
```

## 🚀 API Endpoint Data Generation

### **1. GET /anatomy/body-parts** (30-Part Severity JSON)
```python
async def get_body_parts_severities(current_user: CurrentUser):
    user_id = current_user.user_id
    neo4j_client = get_graph()
    
    # Ensure user graph exists
    neo4j_client.ensure_user_initialized(user_id)
    
    # Get severities via Neo4j query
    severities = neo4j_client.get_body_part_severities(user_id)
    
    # Format for frontend 3D visualization
    body_parts_data = []
    for body_part, severity in severities.items():
        body_parts_data.append({
            "name": body_part,           # e.g., "Heart"
            "severity": severity         # e.g., "mild"
        })
    
    return {
        "user_id": user_id,
        "body_parts": body_parts_data,   # Perfect for 3D model coloring
        "total_parts": 30
    }
```

### **2. GET /anatomy/body-part/{body_part}** (Detailed Info)
```python
async def get_body_part_details(current_user: CurrentUser, body_part: str):
    user_id = current_user.user_id
    neo4j_client = get_graph()
    
    # Get current severity
    severities = neo4j_client.get_body_part_severities(user_id)
    current_severity = severities.get(body_part, "NA")
    
    # Get event history
    event_history = neo4j_client.get_body_part_history(user_id, body_part)
    
    # Get related conditions  
    related_conditions = neo4j_client.get_related_conditions(user_id, body_part)
    
    return {
        "user_id": user_id,
        "body_part": body_part,
        "current_severity": current_severity,
        "statistics": {
            "total_events": len(event_history),
            "severity_distribution": calculate_severity_distribution(event_history)
        },
        "recent_events": event_history[:10],
        "related_conditions": related_conditions[:5]
    }
```

## 🧠 LLM Agent Integration

### **Knowledge Graph Tool for Agents:**
```python
async def _knowledge_graph_query(self, query: str, user_id: str) -> str:
    """Provides body part context to specialist agents"""
    graph_db = get_graph()
    
    # Get current body part severities
    severities = graph_db.get_body_part_severities(user_id)
    
    # Get recent medical timeline
    timeline = graph_db.get_patient_timeline(user_id, limit=10)
    
    # Return structured context for LLM
    context = {
        "body_part_severities": severities,    # All 30 parts with severities
        "recent_events": timeline,             # Recent medical events
        "query_processed": True
    }
    
    return json.dumps(context)  # LLM receives this as tool output
```

### **How Specialist Agents Use This Data:**
1. **Cardiologist** asks: "What's the patient's heart condition?"
2. **Tool Call**: `query_knowledge_graph("heart condition status")`
3. **Tool Returns**: `{"body_part_severities": {"Heart": "mild", ...}, "recent_events": [...]}`
4. **LLM Response**: "Based on your current data, your heart shows mild concerns with recent events showing..."

## 🎯 Key Points

### **✅ What IS LLM-Generated:**
- Expert agent medical opinions and explanations
- Medical entity extraction from complex documents (when enabled)
- Natural language responses to user questions

### **❌ What is NOT LLM-Generated:**
- **Body part severity levels** (rule-based algorithm)
- **Severity calculations** (mathematical formulas)
- **Neo4j graph structure** (programmatic schema)
- **API endpoint responses** (direct database queries)

### **🔄 Data Update Triggers:**
1. **Document Upload** → Extracts entities → Creates Neo4j events → Recalculates severities
2. **Manual Severity Update** → Direct API call → Updates Neo4j relationship
3. **Periodic Recalculation** → Background job → Analyzes recent events → Updates severities

## 📱 Frontend Integration

The data is perfectly structured for 3D model integration:

```javascript
// Frontend code example
const response = await fetch('/anatomy/body-parts', {
    headers: { 'Authorization': `Bearer ${token}` }
});

const { body_parts } = await response.json();

// Apply colors to 3D model based on severity
body_parts.forEach(part => {
    const color = getSeverityColor(part.severity);
    model3D.setBodyPartColor(part.name, color);
});

function getSeverityColor(severity) {
    const colors = {
        'NA': '#gray',
        'normal': '#green',
        'mild': '#yellow', 
        'moderate': '#orange',
        'severe': '#red',
        'critical': '#darkred'
    };
    return colors[severity] || '#gray';
}
```

---

## 📋 Summary

The MediTwin body parts system uses a **hybrid approach**:

1. **Document Processing**: Keyword-based extraction + optional LLM enhancement
2. **Severity Calculation**: Pure algorithmic/rule-based (NO LLM)
3. **Data Storage**: Neo4j graph database with Cypher queries
4. **Expert Opinions**: LLM-powered specialist agents with structured prompts
5. **API Responses**: Direct database queries formatted for frontend consumption

**The severity data itself is mathematically calculated, not LLM-generated, ensuring consistency and reliability for medical applications.**
