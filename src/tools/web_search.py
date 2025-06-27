"""
Web search helper powered by OpenAI `gpt-4o-mini-search-preview`.

The model has a built-in `search` tool. We send the user query, request the
tool, and return the model’s answer (which already incorporates search results
into its reply).

Environment: requires OPENAI_API_KEY.
"""

from __future__ import annotations

import openai, json
from src.config.settings import settings
from src.utils.logging import logger

openai.api_key = settings.openai_api_key
_SEARCH_MODEL = "gpt-4o-mini-search-preview"


def search(query: str, temperature: float = 0.0) -> str:
    """
    Perform an on-the-fly web search and return a concise answer string.

    The model uses its internal search tool – no external API keys needed.
    """
    try:
        response = openai.ChatCompletion.create(
            model=_SEARCH_MODEL,
            messages=[
                {"role": "user", "content": query}
            ],
            tools=[{"type": "search"}],   # instruct model that search tool is allowed
            tool_choice="auto",           # let the model decide if search is required
            temperature=temperature,
        )
        # The assistant’s final answer is in the last choice message
        msg = response.choices[-1].message
        if msg.content:
            return msg.content.strip()
        # If the model instead returned a function_call result, parse content
        if msg.function_call:
            # The "search" function result is in msg.function_call.arguments
            # but preview model typically embeds answer in a follow-up assistant
            # For robustness, just dump the call info.
            return f"Search result: {json.dumps(msg.function_call, indent=2)}"
        return "No search result."
    except Exception as exc:
        logger.error("OpenAI search error: %s", exc)
        return f"Search failed: {exc}"


# Alias for backwards compatibility
search_web = search
