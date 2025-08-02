"""
Configuration for conversation limits and optimized chat storage
"""

import os
from typing import Optional

class ConversationConfig:
    """Configuration for conversation management"""
    
    # Conversation Limits
    MAX_MESSAGES_PER_CONVERSATION = int(os.getenv("MAX_MESSAGES_PER_CONVERSATION", "100"))
    WARNING_THRESHOLD_PERCENT = int(os.getenv("WARNING_THRESHOLD_PERCENT", "90"))
    
    # Cache Settings
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 minutes
    
    # Performance Settings
    DEFAULT_CONTEXT_WINDOW = int(os.getenv("DEFAULT_CONTEXT_WINDOW", "20"))
    MAX_CONVERSATIONS_PER_USER = int(os.getenv("MAX_CONVERSATIONS_PER_USER", "50"))
    
    # Database Settings
    CHAT_COLLECTION_NAME = os.getenv("CHAT_COLLECTION_NAME", "chat_history")
    ENABLE_REDIS_CACHE = os.getenv("ENABLE_REDIS_CACHE", "true").lower() == "true"
    
    # UI Settings
    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    ENABLE_CONVERSATION_WARNINGS = os.getenv("ENABLE_CONVERSATION_WARNINGS", "true").lower() == "true"
    
    @classmethod
    def get_warning_threshold(cls) -> int:
        """Get the message count when to start showing warnings"""
        return int(cls.MAX_MESSAGES_PER_CONVERSATION * cls.WARNING_THRESHOLD_PERCENT / 100)
    
    @classmethod
    def is_conversation_near_limit(cls, message_count: int) -> bool:
        """Check if conversation is near the limit"""
        return message_count >= cls.get_warning_threshold()
    
    @classmethod
    def is_conversation_full(cls, message_count: int) -> bool:
        """Check if conversation has reached the limit"""
        return message_count >= cls.MAX_MESSAGES_PER_CONVERSATION
    
    @classmethod
    def get_remaining_messages(cls, message_count: int) -> int:
        """Get remaining messages in conversation"""
        return max(0, cls.MAX_MESSAGES_PER_CONVERSATION - message_count)


# Create global config instance
conversation_config = ConversationConfig()

# Export constants for backward compatibility
MAX_MESSAGES_PER_CONVERSATION = conversation_config.MAX_MESSAGES_PER_CONVERSATION
WARNING_THRESHOLD = conversation_config.get_warning_threshold()
