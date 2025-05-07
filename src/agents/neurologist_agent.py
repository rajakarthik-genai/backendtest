from prompts import neurologist_prompt
from agents.base_specialist import build_specialist

handle_query = build_specialist(neurologist_prompt)
