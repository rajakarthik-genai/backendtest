"""
Memory Manager - Unified interface for chat memory and user profiles.

This module provides a high-level interface for managing both short-term
conversation memory and long-term user profiles across the application.
"""

import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from src.db.redis_db import get_redis
from src.db.mongo_db import get_mongo
from src.utils.logging import logger


@dataclass
class ConversationSummary:
    """Summary of a conversation for memory purposes."""
    conversation_id: str
    user_id: str
    topic: str
    key_points: List[str]
    timestamp: datetime
    message_count: int


@dataclass
class UserProfile:
    """User profile for long-term memory."""
    user_id: str
    preferences: Dict[str, Any]
    medical_summary: Dict[str, Any]
    conversation_patterns: Dict[str, Any]
    last_updated: datetime


class MemoryManager:
    """
    Unified memory management for conversations and user profiles.
    
    Handles both short-term conversation memory (Redis) and long-term
    user profiles and summaries (MongoDB + Redis).
    """
    
    def __init__(self):
        """Initialize the memory manager."""
        self.redis_client = None
        self.mongo_client = None
    
    async def _ensure_clients(self):
        """Ensure database clients are initialized."""
        if not self.redis_client:
            self.redis_client = get_redis()
        if not self.mongo_client:
            self.mongo_client = await get_mongo()
    
    # Short-term memory (conversation history)
    
    async def add_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add a message to conversation history.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            Success status
        """
        try:
            await self._ensure_clients()
            
            await self.redis_client.store_message(
                user_id, conversation_id, role, content, metadata
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add message to memory: {e}")
            return False
    
    async def get_conversation_history(
        self,
        user_id: str,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get conversation history.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            limit: Optional message limit
            
        Returns:
            List of conversation messages
        """
        try:
            await self._ensure_clients()
            
            conversation = await self.redis_client.get_conversation(user_id, conversation_id)
            
            if not conversation:
                return []
            
            messages = conversation.get("messages", [])
            
            if limit:
                messages = messages[-limit:]
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    async def get_recent_conversations(
        self,
        user_id: str,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent conversations for a user.
        
        Args:
            user_id: User identifier
            days: Number of days to look back
            limit: Maximum number of conversations
            
        Returns:
            List of recent conversations
        """
        try:
            await self._ensure_clients()
            
            conversations = await self.redis_client.get_user_conversations(user_id, limit)
            
            # Filter by date
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_conversations = []
            
            for conv in conversations:
                conv_date = datetime.fromisoformat(conv.get("created_at", ""))
                if conv_date >= cutoff_date:
                    recent_conversations.append(conv)
            
            return recent_conversations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent conversations: {e}")
            return []
    
    async def get_last_user_message(
        self,
        user_id: str,
        conversation_id: str
    ) -> Optional[str]:
        """
        Get the last user message in a conversation.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            
        Returns:
            Last user message content or None
        """
        try:
            messages = await self.get_conversation_history(user_id, conversation_id)
            
            # Find last user message
            for message in reversed(messages):
                if message.get("role") == "user":
                    return message.get("content")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last user message: {e}")
            return None
    
    # Long-term memory (user profiles)
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile from long-term memory.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile or None if not found
        """
        try:
            await self._ensure_clients()
            
            # Try Redis cache first
            cached_profile = await self.redis_client.get_user_data(user_id, "profile")
            
            if cached_profile:
                return UserProfile(**cached_profile)
            
            # Fallback to MongoDB
            profile_data = await self.mongo_client.get_user_profile(user_id)
            
            if profile_data:
                profile = UserProfile(
                    user_id=user_id,
                    preferences=profile_data.get("preferences", {}),
                    medical_summary=profile_data.get("medical_summary", {}),
                    conversation_patterns=profile_data.get("conversation_patterns", {}),
                    last_updated=profile_data.get("last_updated", datetime.utcnow())
                )
                
                # Cache in Redis
                await self.redis_client.store_user_data(
                    user_id, "profile", asdict(profile), ttl=3600
                )
                
                return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    async def update_user_profile(
        self,
        user_id: str,
        preferences: Optional[Dict] = None,
        medical_summary: Optional[Dict] = None,
        conversation_patterns: Optional[Dict] = None
    ) -> bool:
        """
        Update user profile in long-term memory.
        
        Args:
            user_id: User identifier
            preferences: User preferences to update
            medical_summary: Medical summary to update
            conversation_patterns: Conversation patterns to update
            
        Returns:
            Success status
        """
        try:
            await self._ensure_clients()
            
            # Get existing profile or create new one
            existing_profile = await self.get_user_profile(user_id)
            
            if existing_profile:
                profile_data = asdict(existing_profile)
            else:
                profile_data = {
                    "user_id": user_id,
                    "preferences": {},
                    "medical_summary": {},
                    "conversation_patterns": {},
                    "last_updated": datetime.utcnow()
                }
            
            # Update fields
            if preferences:
                profile_data["preferences"].update(preferences)
            if medical_summary:
                profile_data["medical_summary"].update(medical_summary)
            if conversation_patterns:
                profile_data["conversation_patterns"].update(conversation_patterns)
            
            profile_data["last_updated"] = datetime.utcnow()
            
            # Store in MongoDB
            await self.mongo_client.store_user_profile(user_id, profile_data)
            
            # Update Redis cache
            await self.redis_client.store_user_data(
                user_id, "profile", profile_data, ttl=3600
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False
    
    # Conversation summarization
    
    async def summarize_conversation(
        self,
        user_id: str,
        conversation_id: str
    ) -> Optional[ConversationSummary]:
        """
        Generate a summary of a conversation for long-term memory.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            
        Returns:
            Conversation summary or None if failed
        """
        try:
            messages = await self.get_conversation_history(user_id, conversation_id)
            
            if not messages:
                return None
            
            # Simple summarization (could be enhanced with LLM)
            user_messages = [m for m in messages if m.get("role") == "user"]
            
            if not user_messages:
                return None
            
            # Extract key points (simplified)
            key_points = []
            topic = "General medical consultation"
            
            for message in user_messages[:3]:  # Analyze first few messages
                content = message.get("content", "")
                if len(content) > 20:
                    key_points.append(content[:100] + "..." if len(content) > 100 else content)
                    if not topic or topic == "General medical consultation":
                        # Try to extract topic from first substantial message
                        if "heart" in content.lower():
                            topic = "Cardiovascular consultation"
                        elif "brain" in content.lower() or "headache" in content.lower():
                            topic = "Neurological consultation"
                        elif "bone" in content.lower() or "joint" in content.lower():
                            topic = "Orthopedic consultation"
            
            summary = ConversationSummary(
                conversation_id=conversation_id,
                user_id=user_id,
                topic=topic,
                key_points=key_points,
                timestamp=datetime.utcnow(),
                message_count=len(messages)
            )
            
            # Store summary
            await self.mongo_client.store_conversation_summary(user_id, asdict(summary))
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}")
            return None
    
    async def get_conversation_summaries(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ConversationSummary]:
        """
        Get conversation summaries for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of summaries
            
        Returns:
            List of conversation summaries
        """
        try:
            await self._ensure_clients()
            
            summaries_data = await self.mongo_client.get_conversation_summaries(user_id, limit)
            
            summaries = []
            for summary_data in summaries_data:
                summary = ConversationSummary(**summary_data)
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Failed to get conversation summaries: {e}")
            return []
    
    # Memory cleanup
    
    async def cleanup_old_conversations(self, days: int = 90) -> int:
        """
        Clean up old conversation data.
        
        Args:
            days: Age threshold for cleanup
            
        Returns:
            Number of conversations cleaned up
        """
        try:
            await self._ensure_clients()
            
            # This would be implemented based on Redis TTL and MongoDB cleanup
            # For now, return 0 as placeholder
            logger.info(f"Cleanup for conversations older than {days} days initiated")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup old conversations: {e}")
            return 0


# Create default instance
memory_manager = MemoryManager()


# Legacy compatibility functions
async def add_message_to_history(user_id: str, conversation_id: str, role: str, content: str):
    """Legacy compatibility function."""
    return await memory_manager.add_message(user_id, conversation_id, role, content)


async def get_conversation_history(user_id: str, conversation_id: str, limit: Optional[int] = None):
    """Legacy compatibility function."""
    return await memory_manager.get_conversation_history(user_id, conversation_id, limit)


async def get_last_user_question(user_id: str, conversation_id: str):
    """Legacy compatibility function."""
    return await memory_manager.get_last_user_message(user_id, conversation_id)


async def get_long_term_memory(user_id: str):
    """Legacy compatibility function."""
    profile = await memory_manager.get_user_profile(user_id)
    return asdict(profile) if profile else {}


async def update_long_term_memory(user_id: str, data: Dict):
    """Legacy compatibility function."""
    return await memory_manager.update_user_profile(
        user_id,
        preferences=data.get("preferences"),
        medical_summary=data.get("medical_summary"),
        conversation_patterns=data.get("conversation_patterns")
    )
