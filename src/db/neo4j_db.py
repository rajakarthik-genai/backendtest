# Dependencies: Neo4j Python Driver (neo4j)
from neo4j import GraphDatabase

class Neo4jGraphBuilder:
    """
    Neo4j graph client for associating health events or metrics with body part nodes.
    Creates Patient and BodyPart nodes and links them via relationships carrying event details.
    """
    def __init__(self, uri: str, user: str, password: str):
        # Initialize Neo4j driver (Bolt protocol)
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        """Close the Neo4j database connection."""
        self.driver.close()
    
    def _identify_body_part(self, metric_name: str):
        """
        Identify a body part from the metric name if present.
        Returns the standardized body part name or None if not identifiable.
        """
        if not metric_name:
            return None
        name_lower = metric_name.lower()
        # Common body part keywords
        body_parts = ["heart", "lung", "liver", "kidney", "brain", "shoulder", "arm", "leg", "knee", "hip", "spine", "stomach"]
        found_part = None
        for part in body_parts:
            if part in name_lower:
                found_part = part.capitalize()
                # Check for left/right context
                if "right " in name_lower or "right-" in name_lower:
                    if part in name_lower and name_lower.index(part) > 0 and name_lower[name_lower.index(part)-1] != ' ':
                        # part of another word, continue (e.g., "heart" in "earth")
                        pass
                if "right" in name_lower and "right" in name_lower.split():
                    found_part = "Right " + part.capitalize()
                if "left" in name_lower and "left" in name_lower.split():
                    found_part = "Left " + part.capitalize()
                break
        # Additional condition-to-part mapping
        if not found_part:
            if "cardiomegaly" in name_lower:
                found_part = "Heart"
            elif "hepatomegaly" in name_lower:
                found_part = "Liver"
            elif "nephropathy" in name_lower or "renal" in name_lower:
                found_part = "Kidney"
            elif "encephalopathy" in name_lower or "cereb" in name_lower:
                found_part = "Brain"
            elif "pneumonia" in name_lower or "pulmon" in name_lower:
                found_part = "Lung"
        return found_part
    
    def add_health_event(self, patient_id: str, metric_name: str, value=None, timestamp=None):
        """
        Link a health event to the corresponding body part in the Neo4j graph.
        If the metric_name contains or implies a body part, creates/merges a BodyPart node 
        and a Patient node, then creates a HAS_CONDITION relationship from Patient to BodyPart.
        The relationship will carry properties: metric (name of condition/metric), value, timestamp.
        """
        body_part = self._identify_body_part(metric_name)
        if not body_part:
            # If no body part is identified, do nothing (event not spatially linked)
            return
        # Convert timestamp to string (ISO format) for storage, if provided
        ts_str = None
        if timestamp:
            try:
                ts_str = timestamp.isoformat()
            except Exception:
                ts_str = str(timestamp)
        with self.driver.session() as session:
            session.run(
                "MERGE (p:Patient {id: $pid}) "
                "MERGE (b:BodyPart {name: $bname}) "
                "CREATE (p)-[:HAS_CONDITION {metric: $metric, value: $val, timestamp: $ts}]->(b)",
                parameters={
                    "pid": patient_id,
                    "bname": body_part,
                    "metric": metric_name,
                    "val": (value if value is not None else ""), 
                    "ts": (ts_str if ts_str else "")
                }
            )
    
    def add_health_events_batch(self, patient_id: str, records):
        """
        Process a list of records and add relevant health event relationships for each.
        Only records that have an identifiable body part in the metric_name will be linked.
        """
        if records is None:
            return
        for rec in records:
            metric = rec.get("metric_name") or rec.get("name")
            val = rec.get("value", None)
            ts = rec.get("timestamp", None)
            self.add_health_event(patient_id, metric, value=val, timestamp=ts)
