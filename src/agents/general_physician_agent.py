import json
import importlib.resources
from .base_specialist import build_specialist

with importlib.resources.files("src.prompts").joinpath("general_physician_prompt.json").open("r", encoding="utf-8") as f:
    _PROMPT = json.load(f)

handle_query = build_specialist(_PROMPT)

class GeneralPhysicianAgent:
    handle_query = staticmethod(handle_query)

general_physician_agent = GeneralPhysicianAgent()
