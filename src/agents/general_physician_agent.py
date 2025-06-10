import json, importlib.resources
from .base_specialist import build_specialist

with importlib.resources.files("src.prompts").joinpath(
    "general_physician_prompt.json"
).open(encoding="utf-8") as fp:
    _PROMPT = json.load(fp)

handle_query = build_specialist(_PROMPT)
