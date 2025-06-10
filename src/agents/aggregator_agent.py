"""
Aggregator: merges specialist answers into one comprehensive reply
while streaming chunks for SSE.
"""

from typing import List, Generator
import openai, json
from src.config.settings import settings
from src.utils.logging import logger

openai.api_key = settings.openai_api_key


def aggregate(question: str, specialist_outputs: List[str]) -> str:
    """Return a single combined answer (non-streaming)."""
    prompt = (
        "You are the chief physician reviewing multiple specialist opinions.\n"
        f"Patient question: {question}\n\n"
        "Specialist answers:\n"
        + "\n\n".join(specialist_outputs)
        + "\n\nProvide a single, clear, patient-friendly answer."
    )
    resp = openai.ChatCompletion.create(
        model=settings.openai_model_chat,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def aggregate_stream(
    question: str, specialist_outputs: List[str]
) -> Generator[str, None, None]:
    """Stream combined answer chunks (OpenAI delta) suitable for SSE."""
    prompt = (
        "You are the chief physician reviewing multiple specialist opinions.\n"
        f"Patient question: {question}\n\n"
        "Specialist answers:\n"
        + "\n\n".join(specialist_outputs)
        + "\n\nProvide a single, clear, patient-friendly answer."
    )
    stream = openai.ChatCompletion.create(
        model=settings.openai_model_chat,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        temperature=0.3,
    )
    for chunk in stream:
        if chunk.choices:
            delta = chunk.choices[0].delta.get("content")
            if delta:
                yield f"data: {json.dumps({'choices':[{'delta':{'content': delta}}]})}\n\n"
    yield "data: [DONE]\n\n"


# expose default handler (non-stream)
aggregation_agent = aggregate
