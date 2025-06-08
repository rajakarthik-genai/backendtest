import json
import importlib.resources
from src.agents.base_specialist import build_specialist

with importlib.resources.files('src.prompts').joinpath('general_physician_prompt.json').open('r', encoding='utf-8') as f:
    general_physician_prompt = json.load(f)

handle_query = build_specialist(general_physician_prompt)
