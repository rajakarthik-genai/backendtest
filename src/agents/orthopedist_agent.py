import json
import importlib.resources
from src.agents.base_specialist import build_specialist

with importlib.resources.files('src.prompts').joinpath('orthopedist_prompt.json').open('r', encoding='utf-8') as f:
    orthopedist_prompt = json.load(f)

handle_query = build_specialist(orthopedist_prompt)
