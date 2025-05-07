from prompts import orthopedist_prompt
from agents.base_specialist import build_specialist

handle_query = build_specialist(orthopedist_prompt)
