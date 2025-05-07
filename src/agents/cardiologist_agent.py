from prompts import cardiologist_prompt
from agents.base_specialist import build_specialist

handle_query = build_specialist(cardiologist_prompt)
