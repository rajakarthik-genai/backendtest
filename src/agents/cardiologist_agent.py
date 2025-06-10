import json
import importlib.resources
from .base_specialist import build_specialist

with importlib.resources.files("src.prompts").joinpath("cardiologist_prompt.json").open("r", encoding="utf-8") as fp:
    _PROMPT = json.load(fp)

handle_query = build_specialist(_PROMPT)

class CardiologistAgent:
    # Expose the handler as a method
    handle_query = staticmethod(handle_query)

cardiologist_agent = CardiologistAgent()
