"""
Optimized Short-term memory (STM) with array-based conversation storage.
Uses MongoDB with conversation limits similar to Claude.
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from src.db.redis_db import get_redis
from src.utils.logging import logger
from src.config.conversation import conversation_config
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, WriteConcern
from pymongo.errors import DuplicateKeyError
from openai import AsyncOpenAI
from src.core.config import settings

_MAX_CTX = conversation_config.DEFAULT_CONTEXT_WINDOW
MAX_MESSAGES_PER_CONVERSATION = conversation_config.MAX_MESSAGES_PER_CONVERSATION
WARNING_THRESHOLD = conversation_config.get_warning_threshold()


class ShortTermMemory:
    """Optimized STM with array-based storage and conversation limits."""

    def __init__(self):
        """Initialize ShortTermMemory instance."""
        self.mongo_client = None
        self.db = None
        self.redis_client = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Lazy initialization of database connections"""
        if not self._initialized:
            # MongoDB setup
            from src.db.mongodb import get_database
            self.db = await get_database()
            
            # Optimized collection with write concern
            self.chat_collection = self.db.get_collection(
                conversation_config.CHAT_COLLECTION_NAME,
                write_concern=WriteConcern(w=1, j=False)
            )
            
            # Create indexes for performance
            await self._ensure_indexes()
            
            # Redis for caching
            try:
                self.redis_client = get_redis()
            except:
                logger.warning("Redis not available, falling back to MongoDB only")
                self.redis_client = None
            
            self._initialized = True

    async def _ensure_indexes(self):
        """Create optimized indexes for high performance"""
        try:
            # Compound index for queries
            await self.chat_collection.create_index(
                [("user_id", ASCENDING), ("conversation_id", ASCENDING)],
                unique=True,
                background=True
            )
            
            # Index for listing conversations
            await self.chat_collection.create_index(
                [("user_id", ASCENDING), ("updated_at", DESCENDING)],
                background=True
            )
            
            logger.info("Chat storage indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    @staticmethod
    def _key(user: str, doctor: str, conv: str) -> str:
        """Legacy method for backward compatibility"""
        return f"stm:{user}:{doctor}:{conv}"

    async def create_new_conversation(
        self, 
        user_id: str, 
        conversation_id: str = None,
        initial_title: str = ""
    ) -> Dict:
        """Create a new conversation with empty message array"""
        await self._ensure_initialized()
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        now = datetime.utcnow()
        
        document = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "messages": [],
            "message_count": 0,
            "created_at": now,
            "updated_at": now,
            "title": initial_title,
            "is_active": True
        }
        
        try:
            await self.chat_collection.insert_one(document)
            
            # Cache the new conversation
            if self.redis_client:
                cache_key = f"conv:{user_id}:{conversation_id}"
                self.redis_client.client.setex(cache_key, conversation_config.CACHE_TTL_SECONDS, "0")
            
            logger.info(f"Created new conversation {conversation_id} for user {user_id}")
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "remaining_messages": MAX_MESSAGES_PER_CONVERSATION
            }
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return {"success": False, "error": str(e)}

    async def add_message_optimized(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str
    ) -> Tuple[bool, Dict]:
        """
        Add message with limit checking and optimizations
        Returns: (success, response_data)
        """
        await self._ensure_initialized()
        
        timestamp = datetime.utcnow()
        cache_key = f"conv:{user_id}:{conversation_id}"
        
        # Quick check from cache first
        if self.redis_client:
            try:
                cached_count = self.redis_client.client.get(cache_key)
                if cached_count and int(cached_count) >= MAX_MESSAGES_PER_CONVERSATION:
                    return False, {
                        "limit_reached": True,
                        "message": "Conversation limit reached. Please start a new conversation.",
                        "remaining_messages": 0
                    }
            except:
                pass  # Continue if cache fails
        
        # Prepare the message
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        
        # Atomic update with message count check
        result = await self.chat_collection.find_one_and_update(
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "message_count": {"$lt": MAX_MESSAGES_PER_CONVERSATION}
            },
            {
                "$push": {"messages": message},
                "$inc": {"message_count": 1},
                "$set": {"updated_at": timestamp}
            },
            return_document=True
        )
        
        if not result:
            # Check if conversation exists or limit reached
            conv = await self.chat_collection.find_one(
                {"user_id": user_id, "conversation_id": conversation_id},
                {"message_count": 1}
            )
            
            if not conv:
                # Auto-create conversation if it doesn't exist
                await self.create_new_conversation(user_id, conversation_id)
                # Retry adding the message
                return await self.add_message_optimized(user_id, conversation_id, role, content)
            else:
                return False, {
                    "limit_reached": True,
                    "message": "Conversation limit reached. Please start a new conversation.",
                    "remaining_messages": 0
                }
        
        # Generate title if this is the first user message and conversation has no title
        new_count = result["message_count"]
        if (role == "user" and new_count == 1 and 
            not result.get("title")):
            try:
                title = await self.generate_conversation_title(content)
                await self.update_conversation_title(user_id, conversation_id, title)
                logger.info(f"Generated title for conversation {conversation_id}: {title}")
            except Exception as e:
                logger.error(f"Failed to generate title: {e}")
        
        # Update cache
        if self.redis_client:
            try:
                self.redis_client.client.setex(cache_key, conversation_config.CACHE_TTL_SECONDS, str(new_count))
            except:
                pass  # Continue if cache update fails
        
        # Calculate remaining messages
        remaining = MAX_MESSAGES_PER_CONVERSATION - new_count
        
        # Warning near limit
        warning = None
        if conversation_config.is_conversation_near_limit(new_count):
            warning = f"You have {remaining} messages left in this conversation."
        
        return True, {
            "success": True,
            "remaining_messages": remaining,
            "warning": warning,
            "message_count": new_count
        }

    # Legacy static methods for backward compatibility
    @staticmethod
    async def add(user: str, doctor: str, conv: str, role: str, content: str) -> None:
        """Legacy method - redirects to optimized version"""
        instance = ShortTermMemory()
        success, result = await instance.add_message_optimized(user, conv, role, content)
        if not success:
            logger.error(f"Failed to add STM message: {result}")

    @staticmethod
    async def history(user: str, doctor: str, conv: str) -> List[Dict]:
        """Legacy method - get conversation history"""
        instance = ShortTermMemory()
        return await instance.get_recent_messages(user, conversation_id=conv)

    @staticmethod
    async def last_user_msg(user: str, doctor: str, conv: str) -> str | None:
        """Legacy method - get last user message"""
        instance = ShortTermMemory()
        messages = await instance.get_recent_messages(user, conversation_id=conv)
        
        for msg in reversed(messages):
            if msg.get("role") == "user" or msg.get("role") == "human":
                return msg.get("content")
        return None

    @staticmethod
    async def clear(user: str, doctor: str, conv: str) -> None:
        """Legacy method - clear conversation"""
        instance = ShortTermMemory()
        await instance.delete_conversation(user, conv)

    # Instance methods for chat router compatibility
    async def get_recent_messages(
        self, 
        patient_id: str, 
        limit: int = 20, 
        conversation_id: str = "default"
    ) -> List[Dict]:
        """Get recent messages for a patient."""
        await self._ensure_initialized()
        
        try:
            projection = {"messages": {"$slice": -limit}} if limit else {"messages": 1}
            
            doc = await self.chat_collection.find_one(
                {"user_id": patient_id, "conversation_id": conversation_id},
                projection
            )
            
            return doc.get("messages", []) if doc else []
            
        except Exception as e:
            logger.error(f"Failed to get recent messages for patient {patient_id}: {e}")
            return []

    async def store_message(
        self,
        patient_id: str,
        conversation_id: str,
        user_message: str = None,
        assistant_message: str = None,
        metadata: Dict = None,
        timestamp: str = None
    ) -> bool:
        """Store message(s) with limit checking."""
        try:
            success = True
            
            if user_message:
                success, result = await self.add_message_optimized(
                    patient_id, conversation_id, "human", user_message
                )
                if not success:
                    return False
            
            if assistant_message and success:
                success, result = await self.add_message_optimized(
                    patient_id, conversation_id, "assistant", assistant_message
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            return False

    async def check_conversation_limit(
        self,
        user_id: str,
        conversation_id: str
    ) -> Dict:
        """Quick check for conversation limit status"""
        await self._ensure_initialized()
        
        cache_key = f"conv:{user_id}:{conversation_id}"
        
        # Try cache first
        if self.redis_client:
            try:
                cached_count = self.redis_client.client.get(cache_key)
                if cached_count:
                    count = int(cached_count)
                    remaining = MAX_MESSAGES_PER_CONVERSATION - count
                    return {
                        "message_count": count,
                        "remaining_messages": remaining,
                        "is_full": count >= MAX_MESSAGES_PER_CONVERSATION,
                        "warning": remaining <= 10
                    }
            except:
                pass
        
        # Fallback to DB
        try:
            doc = await self.chat_collection.find_one(
                {"user_id": user_id, "conversation_id": conversation_id},
                {"message_count": 1}
            )
            
            if not doc:
                return {"error": "Conversation not found"}
            
            count = doc.get("message_count", 0)
            remaining = MAX_MESSAGES_PER_CONVERSATION - count
            
            # Update cache
            if self.redis_client:
                try:
                    self.redis_client.client.setex(cache_key, conversation_config.CACHE_TTL_SECONDS, str(count))
                except:
                    pass
            
            return {
                "message_count": count,
                "remaining_messages": remaining,
                "is_full": count >= MAX_MESSAGES_PER_CONVERSATION,
                "warning": remaining <= 10
            }
        except Exception as e:
            logger.error(f"Error checking conversation limit: {e}")
            return {"error": str(e)}

    async def get_all_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict]:
        """Get conversations with pagination"""
        await self._ensure_initialized()
        
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$sort": {"updated_at": -1}},
                {"$skip": skip},
                {"$limit": limit},
                {
                    "$project": {
                        "conversation_id": 1,
                        "title": 1,
                        "created_at": 1,
                        "updated_at": 1,
                        "message_count": 1,
                        "last_message": {"$arrayElemAt": ["$messages.content", -1]}
                    }
                }
            ]
            
            conversations = []
            async for doc in self.chat_collection.aggregate(pipeline):
                conversations.append({
                    "conversation_id": doc["conversation_id"],
                    "title": doc.get("title") or doc.get("last_message", "")[:50] + "...",
                    "created_at": doc["created_at"],
                    "updated_at": doc["updated_at"],
                    "message_count": doc.get("message_count", 0),
                    "is_full": doc.get("message_count", 0) >= MAX_MESSAGES_PER_CONVERSATION
                })
            
            return conversations
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []

    async def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Delete a conversation"""
        await self._ensure_initialized()
        
        try:
            result = await self.chat_collection.delete_one({
                "user_id": user_id,
                "conversation_id": conversation_id
            })
            
            # Clear cache
            if self.redis_client:
                cache_key = f"conv:{user_id}:{conversation_id}"
                try:
                    self.redis_client.client.delete(cache_key)
                except:
                    pass
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False

    @staticmethod
    def get_context(messages: List[Dict], limit: int = _MAX_CTX) -> str:
        """Static method to get context from messages"""
        if not messages:
            return ""
        
        # Get the last N messages for context
        recent_messages = messages[-limit:] if len(messages) > limit else messages
        
        context_parts = []
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)

    @staticmethod
    async def get_context(user_id: str, session_id: str, doctor_id: str = "default") -> Dict[str, Any]:
        """Get short-term memory context for a user session."""
        instance = ShortTermMemory()
        history = await instance.get_recent_messages(user_id, conversation_id=session_id)
        last_msg = None
        
        for msg in reversed(history):
            if msg.get("role") in ["user", "human"]:
                last_msg = msg.get("content")
                break
        
        return {
            "recent_messages": history,
            "last_user_message": last_msg,
            "message_count": len(history)
        }

    async def generate_conversation_title(self, first_user_message: str) -> str:
        """Generate a short title for conversation based on first message"""
        try:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_SIMPLE,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates short, concise titles for medical conversations. Generate a title of maximum 4-5 words that summarizes the main topic or concern. Respond with only the title, no quotes or additional text."
                    },
                    {
                        "role": "user", 
                        "content": f"Create a short title for this medical question: {first_user_message}"
                    }
                ],
                max_tokens=20,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            # Ensure title is not too long
            if len(title) > 50:
                title = title[:47] + "..."
            
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            # Fallback to truncated message
            return first_user_message[:30] + "..." if len(first_user_message) > 30 else first_user_message

    async def update_conversation_title(self, user_id: str, conversation_id: str, title: str) -> bool:
        """Update conversation title"""
        await self._ensure_initialized()
        
        try:
            result = await self.chat_collection.update_one(
                {"user_id": user_id, "conversation_id": conversation_id},
                {"$set": {"title": title, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            return False

    async def cleanup(self):
        """Cleanup connections"""
        if self.mongo_client:
            self.mongo_client.close()


def get_short_term_memory():
    """Factory function to get ShortTermMemory instance"""
    return ShortTermMemory()
