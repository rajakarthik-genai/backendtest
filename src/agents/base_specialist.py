from __future__ import annotations
import json, openai
from typing import Callable
from utils.logging import logger
from tools import web_search, vector_store, knowledge_graph, document_db

def build_specialist(prompt_dict: dict) -> Callable[[str, str], str]:
    """
    Factory → returns a .handle_query(user_id, query) function
    bound to supplied prompt.
    """
    functions = [
        {
            "name": "search_web",
            "description": "Search the web for up-to-date info.",
            "parameters": {"type": "object","properties":{"query":{"type":"string"}},"required":["query"]},
        },
        {
            "name": "query_vector_db",
            "description": "Semantic search in medical knowledge base.",
            "parameters": {"type": "object","properties":{"query":{"type":"string"}},"required":["query"]},
        },
        {
            "name": "query_graph",
            "description": "Query medical knowledge graph.",
            "parameters": {"type": "object","properties":{"query":{"type":"string"}},"required":["query"]},
        },
        {
            "name": "query_document_db",
            "description": "Fetch patient record by type.",
            "parameters": {"type": "object","properties":{"record_type":{"type":"string"}},"required":["record_type"]},
        },
    ]

    def _run_tool(name: str, user_id: str, args: dict):
        if name == "search_web":
            return web_search.search(args.get("query", ""))
        if name == "query_vector_db":
            return vector_store.query_text(args.get("query", ""))
        if name == "query_graph":
            return knowledge_graph.query_natural(args.get("query", ""))
        if name == "query_document_db":
            return document_db.get_patient_record(user_id, args.get("record_type", ""))
        return "Tool unavailable."

    def handle_query(user_id: str, query: str) -> str:
        messages = [
            {"role": "system", "content": prompt_dict["system"]},
            {"role": "user", "content": query},
        ]
        while True:
            resp = openai.ChatCompletion.create(
                model="gpt-4-0613",
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=0.3,
            )
            msg = resp.choices[0].message
            if msg.get("function_call"):
                fn = msg["function_call"]["name"]
                args = json.loads(msg["function_call"].get("arguments", "{}") or "{}")
                result = _run_tool(fn, user_id, args)
                messages.extend([
                    {"role": "assistant", "content": None,
                     "function_call": {"name": fn, "arguments": json.dumps(args)}},
                    {"role": "function", "name": fn, "content": result},
                ])
                continue
            return msg.get("content", "")
    return handle_query
