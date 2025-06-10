"""
Factory helper to build a specialist agent that can:
• reason step-by-step with its long prompt
• call domain-agnostic tools (web search, vector search, graph query, doc DB)
• return a final answer string
"""

from __future__ import annotations

import json
import openai
from typing import Callable, Dict, List

from src.config.settings import settings
from src.tools import document_db, knowledge_graph, vector_store, web_search
from src.utils.logging import logger

openai.api_key = settings.openai_api_key

# --------------------------------------------------------------------------- #
# Tool spec helpers (OpenAI function-calling JSON schemas)
# --------------------------------------------------------------------------- #
_tools_schema: List[dict] = [
    {
        "name": "search_web",
        "description": "Search the web for current medical guidance.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "query_vector_db",
        "description": "Semantic similarity search in Milvus.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "query_graph",
        "description": "Run a natural-language query against the Neo4j graph.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "query_document_db",
        "description": "Retrieve a patient record of a given type "
                       "(e.g. 'labs', 'imaging').",
        "parameters": {
            "type": "object",
            "properties": {"record_type": {"type": "string"}},
            "required": ["record_type"],
        },
    },
]


def _execute_tool(user_id: str, name: str, args: Dict) -> str:
    """Dispatch a tool call to the correct helper."""
    if name == "search_web":
        return web_search.search(args["query"])
    if name == "query_vector_db":
        return vector_store.query_text(args["query"])
    if name == "query_graph":
        return knowledge_graph.query_natural(args["query"])
    if name == "query_document_db":
        return document_db.get_patient_record(user_id, args["record_type"])
    return f"Tool '{name}' is unavailable."


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
def build_specialist(prompt: Dict) -> Callable[[str, str], str]:
    """
    Build a specialist handler.

    Args:
        prompt: dict with keys 'system' (system prompt) and 'agent' (name).

    Returns:
        handle_query(user_id, question) → str
    """

    system_msg = (
        prompt.get("system")
        or f"You are {prompt.get('agent','Medical Specialist')}."
    )

    def handle_query(user_id: str, question: str) -> str:
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": question},
        ]
        while True:
            resp = openai.ChatCompletion.create(
                model=settings.openai_model_chat,
                messages=messages,
                functions=_tools_schema,
                function_call="auto",
                temperature=0.2,
            )
            msg = resp.choices[0].message
            if fc := msg.get("function_call"):
                fn_name = fc["name"]
                fn_args = json.loads(fc.get("arguments") or "{}")
                logger.info("%s: tool-call %s(%s)", prompt["agent"], fn_name, fn_args)
                result = _execute_tool(user_id, fn_name, fn_args)
                # append assistant call + function result
                messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "function_call": {"name": fn_name, "arguments": json.dumps(fn_args)},
                    }
                )
                messages.append({"role": "function", "name": fn_name, "content": result})
                continue  # LLM will see function result
            # final answer
            return msg.get("content", "").strip()

    return handle_query
