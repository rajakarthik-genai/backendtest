# Dependencies: none (uses MongoDB from mongo_db.py)
from datetime import datetime

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
