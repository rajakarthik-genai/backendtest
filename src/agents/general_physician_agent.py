from prompts import general_physician_prompt
from agents.base_specialist import build_specialist

handle_query = build_specialist(general_physician_prompt)
