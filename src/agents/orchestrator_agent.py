"""
High-level planner → decides which specialist(s) to invoke via
OpenAI function-calling and finally streams aggregated answer
back to API layer.
"""
from __future__ import annotations
import json, openai
from utils.logging import logger
from prompts import orchestrator_prompt
from memory.memory_manager import (
    get_conversation_history,
    get_long_term_memory,
    add_message_to_history,
)
from agents import (
    cardiologist_agent,
    general_physician_agent,
    orthopedist_agent,
    neurologist_agent,
    aggregator_agent,
)

# -------- function registry -------- #
def _call_specialist(func_name: str, user_id: str, query: str) -> str:
    mapping = {
        "cardiologist":        cardiologist_agent.handle_query,
        "general_physician":   general_physician_agent.handle_query,
        "orthopedist":         orthopedist_agent.handle_query,
        "neurologist":         neurologist_agent.handle_query,
    }
    return mapping[func_name](user_id, query)


class OrchestratorAgent:
    """Singleton orchestration engine."""

    def __init__(self):
        self.prompt = orchestrator_prompt
        self.functions_schema = self._build_fn_schema()

    # --------------------------------------------------------
    def _build_fn_schema(self) -> list[dict]:
        base = lambda name, desc: {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        }
        aggregator = {
            "name": "aggregator",
            "description": "Merge specialist answers into final reply.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of specialist answers.",
                    }
                },
                "required": ["answers"],
            },
        }
        return [
            base("cardiologist", "Heart & circulatory issues."),
            base("general_physician", "General medical overview."),
            base("orthopedist", "Bones, joints, muscles."),
            base("neurologist", "Brain & nervous system."),
            aggregator,
        ]

    # --------------------------------------------------------
    def handle_request(self, user_id: str, user_msg: str):
        """
        Generator → yields SSE chunks comprising the final answer.

        Loop:
            - call GPT-4 function-calling
            - if function requested → run specialist / aggregator
        """
        messages: list[dict] = [
            {"role": "system", "content": self.prompt["system"]},
        ]
        # add memory
        if (ltm := get_long_term_memory(user_id)):
            messages.append({"role": "system", "content": f"User context: {ltm}"})
        messages.extend(get_conversation_history(user_id))
        messages.append({"role": "user", "content": user_msg})

        collected: list[str] = []

        while True:
            resp = openai.ChatCompletion.create(
                model="gpt-4-0613",
                messages=messages,
                functions=self.functions_schema,
                function_call="auto",
            )
            msg = resp.choices[0].message
            if msg.get("function_call"):
                fn_name = msg["function_call"]["name"]
                args    = json.loads(msg["function_call"].get("arguments", "{}") or "{}")
                logger.debug(f"Orchestrator → call {fn_name} {args}")
                if fn_name == "aggregator":
                    # stream aggregator answer
                    for chunk in aggregator_agent.combine_answers(user_id, collected):
                        yield chunk
                    break
                # specialist
                answer = _call_specialist(fn_name, user_id, args.get("query", user_msg))
                collected.append(answer)
                # push tool result back as function message
                messages.extend([
                    {"role": "assistant", "content": None,
                     "function_call": {"name": fn_name, "arguments": json.dumps(args)}},
                    {"role": "function", "name": fn_name, "content": answer},
                ])
                continue
            # direct answer (rare)
            full = msg.get("content", "")
            for tok in full.split():
                yield f"data: {{\"choices\":[{{\"delta\":{{\"content\":\"{tok} \"}}}}]}}\n\n"
            yield "data: [DONE]\n\n"
            add_message_to_history(user_id, "assistant", full)
            break


# public singleton
orchestrator_agent = OrchestratorAgent()
