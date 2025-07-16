"""
Web search helper powered by OpenAI.

Uses the standard OpenAI chat completion for medical information searches.
Environment: requires OPENAI_API_KEY.
"""

from __future__ import annotations

import json

# Safe import approach
try:
    from src.config.settings import settings
    from src.utils.logging import logger
    from openai import AsyncOpenAI
    
    # Initialize async OpenAI client with fallback
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
    except Exception:
        client = None
        
except ImportError as e:
    # Fallback for when dependencies are not available
    settings = None
    logger = None
    client = None
    print(f"Warning: Could not import dependencies: {e}")


async def search(query: str, temperature: float = 0.0) -> str:
    """
    Perform web search using OpenAI for medical information.
    
    Args:
        query: Search query
        temperature: Model temperature for response generation
        
    Returns:
        Search results and summary
    """
    if not client or not settings:
        return "Search unavailable: OpenAI client not initialized"
        
    try:
        # Use the configured search model
        response = await client.chat.completions.create(
            model=settings.openai_model_search,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a medical research assistant. Provide accurate, evidence-based medical information based on the user's query. Focus on current medical knowledge and best practices."
                },
                {
                    "role": "user", 
                    "content": f"Provide information about: {query}"
                }
            ],
            temperature=temperature,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content
        if logger:
            logger.info(f"Web search completed for query: {query[:50]}...")
        return result
        
    except Exception as e:
        error_msg = f"Web search failed for query '{query}': {e}"
        if logger:
            logger.error(error_msg)
        return f"Search unavailable: {str(e)}"


# Synchronous wrapper for backwards compatibility
def search_sync(query: str, temperature: float = 0.0) -> str:
    """Synchronous version of search function."""
    import asyncio
    try:
        return asyncio.run(search(query, temperature))
    except Exception as e:
        error_msg = f"Sync web search failed: {e}"
        if logger:
            logger.error(error_msg)
        return f"Search failed: {str(e)}"


# Alias for backwards compatibility
search_web = search
