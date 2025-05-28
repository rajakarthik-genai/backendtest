# File: db/neo4j_db.py
from neo4j import GraphDatabase

class Neo4jDB:
    """
    Neo4j client for graph modeling of patient health events.
    """
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_patient(self, user_id, first_name, last_name, dob=None, gender=None):
        """
        Create or merge a Patient node with the given properties.
        """
        with self.driver.session() as session:
            result = session.write_transaction(
                self._create_patient_tx, user_id, first_name, last_name, dob, gender
            )
            return result

    @staticmethod
    def _create_patient_tx(tx, user_id, first_name, last_name, dob, gender):
        query = (
            "MERGE (p:Patient {user_id: $user_id}) "
            "SET p.first_name = $first_name, p.last_name = $last_name, "
            "p.dob = $dob, p.gender = $gender "
            "RETURN p"
        )
        res = tx.run(
            query, user_id=user_id,
            first_name=first_name, last_name=last_name,
            dob=dob, gender=gender
        )
        record = res.single()
        return record["p"] if record else None

    def create_condition(self, name, description=None):
        """
        Create or merge a Condition node.
        """
        with self.driver.session() as session:
            result = session.write_transaction(
                self._create_condition_tx, name, description
            )
            return result

    @staticmethod
    def _create_condition_tx(tx, name, description):
        query = (
            "MERGE (c:Condition {name: $name}) "
            "SET c.description = $description "
            "RETURN c"
        )
        res = tx.run(query, name=name, description=description)
        record = res.single()
        return record["c"] if record else None

    def link_patient_condition(self, user_id, condition_name):
        """
        Create a HAS_CONDITION relationship between a Patient and a Condition.
        """
        with self.driver.session() as session:
            session.write_transaction(
                self._link_patient_condition_tx, user_id, condition_name
            )

    @staticmethod
    def _link_patient_condition_tx(tx, user_id, condition_name):
        query = (
            "MATCH (p:Patient {user_id: $user_id}), (c:Condition {name: $condition_name}) "
            "MERGE (p)-[:HAS_CONDITION]->(c)"
        )
        tx.run(query, user_id=user_id, condition_name=condition_name)

    def create_event(self, event_id, patient_id, event_type, description=None, timestamp=None):
        """
        Create or merge an Event node and link it to a Patient.
        """
        with self.driver.session() as session:
            session.write_transaction(
                self._create_event_tx, event_id, patient_id, event_type, description, timestamp
            )

    @staticmethod
    def _create_event_tx(tx, event_id, patient_id, event_type, description, timestamp):
        query = (
            "MERGE (e:Event {id: $event_id}) "
            "SET e.event_type = $event_type, e.description = $description, e.timestamp = $timestamp "
            "WITH e "
            "MATCH (p:Patient {user_id: $patient_id}) "
            "MERGE (p)-[:HAS_EVENT]->(e)"
        )
        tx.run(query, event_id=event_id, patient_id=patient_id,
               event_type=event_type, description=description, timestamp=timestamp)

    def get_patient_conditions(self, user_id):
        """
        Return all conditions linked to a patient.
        """
        with self.driver.session() as session:
            result = session.run(
                "MATCH (p:Patient {user_id: $user_id})-[:HAS_CONDITION]->(c:Condition) "
                "RETURN c.name AS condition", user_id=user_id
            )
            return [record["condition"] for record in result]

    def get_patient_events(self, user_id):
        """
        Return all events (with types) for a patient, ordered by timestamp.
        """
        with self.driver.session() as session:
            result = session.run(
                "MATCH (p:Patient {user_id: $user_id})-[:HAS_EVENT]->(e:Event) "
                "RETURN e.event_type AS type, e.timestamp AS when "
                "ORDER BY e.timestamp", user_id=user_id
            )
            return [{"type": record["type"], "when": record["when"]} for record in result]
