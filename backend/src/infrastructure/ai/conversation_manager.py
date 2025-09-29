"""
Conversation Management System

Manages chat conversations using existing ChatThread and ChatMessage models.
Provides intelligent conversation threading and memory management.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, delete, update
from sqlalchemy.orm import selectinload

from ...shared.exceptions import NotFoundError, ValidationError, ProcessingError
from ...shared.config import get_settings
from ..database.models import ChatThread, ChatMessage

logger = logging.getLogger(__name__)


class ConversationContext:
    """Represents conversation context for AI processing."""
    
    def __init__(
        self,
        messages: List[Dict[str, Any]],
        conversation_id: int,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.messages = messages
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.token_count = sum(len(msg.get('content', '').split()) for msg in messages)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary representation."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "messages": self.messages,
            "token_count": self.token_count,
            "metadata": self.metadata
        }


class ConversationManager:
    """Manages chat conversations and message persistence."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
    
    async def create_conversation(
        self,
        user_id: int,
        title: str,
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> ChatThread:
        """Create a new conversation."""
        try:
            conversation = ChatThread(
                user_id=user_id,
                title=title,
                category=category,
                tags=tags,
                status="active"
            )
            
            self.session.add(conversation)
            await self.session.flush()  # Get the ID
            await self.session.refresh(conversation)
            
            return conversation
                
        except Exception as e:
            raise ProcessingError(f"Failed to create conversation: {str(e)}")
    
    async def add_message(
        self,
        conversation_id: int,
        user_id: Optional[int],
        content: str,
        role: str = "user",
        message_type: str = "text",
        processing_time_ms: Optional[int] = None,
        model_used: Optional[str] = None
    ) -> ChatMessage:
        """Add a message to a conversation."""
        try:
            message = ChatMessage(
                thread_id=conversation_id,
                user_id=user_id or 1,  # Default user for AI messages
                content=content,
                role=role,
                message_type=message_type,
                processing_time_ms=processing_time_ms or 0,
                ai_model=model_used
            )
            
            self.session.add(message)
            await self.session.flush()
            await self.session.refresh(message)
            
            # Update conversation's last activity
            conversation = await self.session.get(ChatThread, conversation_id)
            if conversation:
                conversation.updated_at = datetime.utcnow()
                conversation.last_message_at = datetime.utcnow()
                conversation.message_count += 1
            
            return message
                
        except Exception as e:
            raise ProcessingError(f"Failed to add message: {str(e)}")
    
    async def get_conversation_messages(
        self,
        conversation_id: int,
        page: int = 1,
        per_page: int = 50
    ) -> List[ChatMessage]:
        """Get messages for a conversation with pagination."""
        try:
            offset = (page - 1) * per_page
            
            query = (
                select(ChatMessage)
                .where(ChatMessage.thread_id == conversation_id)
                .order_by(ChatMessage.created_at)
                .limit(per_page)
                .offset(offset)
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            raise ProcessingError(f"Failed to get conversation messages: {str(e)}")
    
    async def list_conversations(
        self,
        user_id: int,
        category: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        include_archived: bool = False
    ) -> List[ChatThread]:
        """List conversations for a user. Excludes archived/deleted conversations by default."""
        try:
            query = select(ChatThread).where(ChatThread.user_id == user_id)
            
            if category:
                query = query.where(ChatThread.category == category)
            
            if status:
                query = query.where(ChatThread.status == status)
            elif not include_archived:
                # Exclude deleted conversations by default
                query = query.where(ChatThread.status != 'deleted')
            
            # Order by most recent activity
            query = (
                query.order_by(desc(ChatThread.updated_at))
                .limit(per_page)
                .offset((page - 1) * per_page)
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            raise ProcessingError(f"Failed to list conversations: {str(e)}")
    
    async def get_conversation(
        self,
        conversation_id: int,
        user_id: Optional[int] = None
    ) -> Optional[ChatThread]:
        """Get a specific conversation by ID."""
        try:
            query = select(ChatThread).where(ChatThread.id == conversation_id)
            
            if user_id is not None:
                # Verify user has access to this conversation
                query = query.where(ChatThread.user_id == user_id)
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise ProcessingError(f"Failed to get conversation: {str(e)}")
    
    async def get_conversation_context(
        self,
        conversation_id: int,
        max_messages: int = 10,
        include_summary: bool = True
    ) -> ConversationContext:
        """Get conversation context for AI processing."""
        try:
            # Get recent messages
            messages_query = (
                select(ChatMessage)
                .where(ChatMessage.thread_id == conversation_id)
                .order_by(desc(ChatMessage.created_at))
                .limit(max_messages)
            )
            
            messages_result = await self.session.execute(messages_query)
            messages = list(reversed(messages_result.scalars().all()))
            
            # Get conversation metadata
            conversation = await self.session.get(ChatThread, conversation_id)
            if not conversation:
                raise NotFoundError(f"Conversation {conversation_id} not found")
            
            # Convert messages to context format
            context_messages = []
            for msg in messages:
                context_messages.append({
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "message_type": msg.message_type
                })
            
            # Build context metadata
            metadata = {
                "conversation_title": conversation.title,
                "conversation_category": conversation.category,
                "message_count": len(context_messages),
                "last_updated": conversation.updated_at.isoformat() if conversation.updated_at else None
            }
            
            return ConversationContext(
                messages=context_messages,
                conversation_id=conversation_id,
                user_id=conversation.user_id,
                metadata=metadata
            )
            
        except Exception as e:
            raise ProcessingError(f"Failed to get conversation context: {str(e)}")

    async def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        Delete a conversation thread and all its messages.
        
        Args:
            conversation_id: The conversation thread ID
            user_id: The user ID (for security verification)
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            # First verify the conversation exists and belongs to the user
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                return False
            
            # Delete all messages in the conversation first
            messages_delete = delete(ChatMessage).where(ChatMessage.thread_id == conversation_id)
            await self.session.execute(messages_delete)
            
            # Delete the conversation thread
            conversation_delete = delete(ChatThread).where(
                and_(ChatThread.id == conversation_id, ChatThread.user_id == user_id)
            )
            await self.session.execute(conversation_delete)
            
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return False

    async def soft_delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        Soft delete a conversation (mark as deleted but keep in database).
        
        Args:
            conversation_id: The conversation thread ID
            user_id: The user ID (for security verification)
            
        Returns:
            bool: True if soft deletion was successful
        """
        try:
            # Update the conversation status to deleted
            update_stmt = (
                update(ChatThread)
                .where(and_(ChatThread.id == conversation_id, ChatThread.user_id == user_id))
                .values(
                    status='deleted',
                    archived_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            result = await self.session.execute(update_stmt)
            
            if result.rowcount == 0:
                return False
                
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error soft deleting conversation {conversation_id}: {str(e)}")
            return False