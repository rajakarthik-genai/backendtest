import os
from typing import List
from openai import AsyncOpenAI
from src.core.config import settings

async def llm_get_body_parts_for_region(region: str, body_part_list: List[str]) -> List[str]:
    """
    Use LLM to determine which body parts belong to a given region, based on the current taxonomy.
    """
    prompt = f"""
You are a medical knowledge assistant. Given the following list of body parts:
{body_part_list}

If a user requests the region '{region}', which body parts should be included? Respond with a JSON array of body part names, using only the provided list. Do not include any explanation or extra text.
"""
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL_SIMPLE,
        messages=[
            {"role": "system", "content": "You are a medical knowledge assistant."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=300
    )
    content = response.choices[0].message.content.strip()
    # Remove markdown if present
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    import json
    try:
        result = json.loads(content)
        if isinstance(result, list):
            return result
        # If the LLM returns a dict with a key, try to extract the list
        if isinstance(result, dict):
            for v in result.values():
                if isinstance(v, list):
                    return v
        return []
    except Exception:
        return []

async def llm_calculate_severity(body_part_or_region: str, events: list) -> str:
    """
    Use LLM to assess the overall severity for a body part or region given recent events.
    Returns one of: normal, mild, moderate, severe, critical.
    """
    import json
    # Prepare event summary for the prompt
    if not events:
        return "normal"
    event_lines = []
    for event in events:
        line = f"- {event.get('title', event.get('description', 'Event'))} (severity: {event.get('severity', 'unknown')}, date: {event.get('timestamp', '')})"
        event_lines.append(line)
    events_text = "\n".join(event_lines)
    prompt = f"""
You are a medical AI assistant. Given these recent events for the {body_part_or_region}:
{events_text}

What is the current overall severity for this {body_part_or_region}? Respond with one word: normal, mild, moderate, severe, or critical. Do not include any explanation or extra text.
"""
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL_SIMPLE,
        messages=[
            {"role": "system", "content": "You are a medical AI assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=10
    )
    content = response.choices[0].message.content.strip().lower()
    # Only accept valid severities
    valid = ["normal", "mild", "moderate", "severe", "critical"]
    for v in valid:
        if v in content:
            return v
    return "normal" 