"""
Combine specialist outputs into one coherent final reply.
"""
from __future__ import annotations
import json, openai
from prompts import aggregator_prompt
from utils.logging import logger
from memory.memory_manager import add_message_to_history, get_last_user_question


def combine_answers(user_id: str, answers: list[str]):
    """Yield SSE stream chunks."""
    user_q = get_last_user_question(user_id) or "<question unavailable>"
    messages = [
        {"role": "system", "content": aggregator_prompt["system"]},
        {
            "role": "user",
            "content": (
                f"User question: {user_q}\n\nSpecialist inputs:\n" +
                "\n".join(answers) +
                "\n\nCraft a single comprehensive answer."
            ),
        },
    ]
    full = ""
    try:
        stream = openai.ChatCompletion.create(
            model="gpt-4-0613", messages=messages, stream=True
        )
        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta.get("content")
                if delta:
                    full += delta
                    yield f"data: {json.dumps({'choices':[{'delta':{'content':delta}}]})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        logger.error(f"Aggregator error: {exc}")
        yield "data: Aggregation failed.\n\n"
        yield "data: [DONE]\n\n"
    finally:
        if full:
            add_message_to_history(user_id, "assistant", full)
