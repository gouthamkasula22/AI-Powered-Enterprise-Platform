"""
Enhanced Chat Repository Implementations

This module provides the implementations of the repository interfaces
for chat functionality using modern SQLAlchemy with enhanced entities.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Import enhanced domain entities
from ...domain.entities.chat.chat_entities import (
    ChatThread as ChatThreadEntity,
    ChatMessage as ChatMessageEntity,
    Document as DocumentEntity,
    ThreadStatus, ThreadCategory, MessageStatus, ProcessingStatus
)

# Import repository interfaces 
from ...domain.chat.repositories import (
    ChatThreadRepository, 
    ChatMessageRepository,
    DocumentRepository
)

# Import database models
from ..database.models.chat_models import (
    ChatThread as ChatThreadModel,
    ChatMessage as ChatMessageModel,
    Document as DocumentModel
)


class SQLAChatThreadRepository(ChatThreadRepository):
    """SQLAlchemy implementation of ChatThreadRepository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _model_to_entity(self, db_thread: ChatThreadModel) -> ChatThreadEntity:
        """Convert database model to domain entity."""
        return ChatThreadEntity(
            id=db_thread.id,
            user_id=db_thread.user_id,
            title=db_thread.title,
            status=ThreadStatus(db_thread.status),
            category=ThreadCategory(db_thread.category),
            tags=db_thread.tags or [],
            is_favorite=db_thread.is_favorite,
            is_shared=db_thread.is_shared,
            parent_thread_id=db_thread.parent_thread_id,
            thread_order=db_thread.thread_order,
            access_level=db_thread.access_level,
            sharing_permissions=db_thread.sharing_permissions or {},
            created_at=db_thread.created_at,
            updated_at=db_thread.updated_at,
            last_message_at=db_thread.last_message_at,
            archived_at=db_thread.archived_at,
            message_count=db_thread.message_count,
            document_count=db_thread.document_count,
            total_tokens_used=db_thread.total_tokens_used,
            meta_data=db_thread.meta_data or {},
            ai_configuration=db_thread.ai_configuration or {}
        )
    
    def _entity_to_model_data(self, thread: ChatThreadEntity) -> dict:
        """Convert domain entity to model data for database operations."""
        return {
            'user_id': thread.user_id,
            'title': thread.title,
            'status': thread.status.value,
            'category': thread.category.value,
            'tags': thread.tags,
            'is_favorite': thread.is_favorite,
            'is_shared': thread.is_shared,
            'parent_thread_id': thread.parent_thread_id,
            'thread_order': thread.thread_order,
            'access_level': thread.access_level,
            'sharing_permissions': thread.sharing_permissions,
            'updated_at': thread.updated_at or datetime.utcnow(),
            'last_message_at': thread.last_message_at,
            'archived_at': thread.archived_at,
            'message_count': thread.message_count,
            'document_count': thread.document_count,
            'total_tokens_used': thread.total_tokens_used,
            'meta_data': thread.meta_data,
            'ai_configuration': thread.ai_configuration
        }

    async def create(self, thread: ChatThreadEntity) -> ChatThreadEntity:
        """Create a new chat thread."""
        db_thread = ChatThreadModel(
            **self._entity_to_model_data(thread),
            created_at=datetime.utcnow()
        )
        
        self.session.add(db_thread)
        await self.session.flush()
        await self.session.refresh(db_thread)
        
        return self._model_to_entity(db_thread)

    async def get_by_id(self, thread_id: int) -> Optional[ChatThreadEntity]:
        """Get a chat thread by ID."""
        stmt = select(ChatThreadModel).where(ChatThreadModel.id == thread_id)
        result = await self.session.execute(stmt)
        db_thread = result.scalar_one_or_none()
        
        return self._model_to_entity(db_thread) if db_thread else None

    async def update(self, thread: ChatThreadEntity) -> ChatThreadEntity:
        """Update an existing chat thread."""
        if not thread.id:
            raise ValueError("Cannot update thread without ID")
            
        stmt = (
            update(ChatThreadModel)
            .where(ChatThreadModel.id == thread.id)
            .values(**self._entity_to_model_data(thread))
        )
        
        await self.session.execute(stmt)
        
        # Return updated thread
        updated_thread = await self.get_by_id(thread.id)
        if updated_thread is None:
            raise ValueError(f"Thread with ID {thread.id} not found after update")
        return updated_thread

    async def delete(self, thread_id: int) -> bool:
        """Delete a chat thread."""
        stmt = delete(ChatThreadModel).where(ChatThreadModel.id == thread_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_by_user(
        self, 
        user_id: int, 
        status: Optional[ThreadStatus] = None,
        category: Optional[ThreadCategory] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatThreadEntity]:
        """Get chat threads for a user with filtering options."""
        stmt = select(ChatThreadModel).where(ChatThreadModel.user_id == user_id)
        
        if status:
            stmt = stmt.where(ChatThreadModel.status == status.value)
        if category:
            stmt = stmt.where(ChatThreadModel.category == category.value)
            
        stmt = stmt.offset(offset).limit(limit).order_by(ChatThreadModel.updated_at.desc())
        
        result = await self.session.execute(stmt)
        db_threads = result.scalars().all()
        
        return [self._model_to_entity(db_thread) for db_thread in db_threads]

    async def get_by_user_with_stats(self, user_id: int) -> List[Tuple[ChatThreadEntity, Dict[str, Any]]]:
        """Get chat threads for a user with statistics."""
        threads = await self.get_by_user(user_id)
        result = []
        
        for thread in threads:
            stats = {
                'message_count': thread.message_count,
                'document_count': thread.document_count,
                'total_tokens': thread.total_tokens_used,
                'last_activity': thread.last_message_at,
                'is_favorite': thread.is_favorite,
                'is_shared': thread.is_shared
            }
            result.append((thread, stats))
            
        return result

    async def search_threads(
        self, 
        user_id: int, 
        query: str,
        categories: Optional[List[ThreadCategory]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[ChatThreadEntity]:
        """Search chat threads by content, title, or tags."""
        stmt = select(ChatThreadModel).where(ChatThreadModel.user_id == user_id)
        
        # Search in title
        stmt = stmt.where(ChatThreadModel.title.ilike(f"%{query}%"))
        
        if categories:
            category_values = [cat.value for cat in categories]
            stmt = stmt.where(ChatThreadModel.category.in_(category_values))
            
        if tags:
            # PostgreSQL array contains search
            for tag in tags:
                stmt = stmt.where(ChatThreadModel.tags.contains([tag]))
        
        stmt = stmt.limit(limit).order_by(ChatThreadModel.updated_at.desc())
        
        result = await self.session.execute(stmt)
        db_threads = result.scalars().all()
        
        return [self._model_to_entity(db_thread) for db_thread in db_threads]

    async def get_favorites(self, user_id: int) -> List[ChatThreadEntity]:
        """Get favorite threads for a user."""
        stmt = (
            select(ChatThreadModel)
            .where(ChatThreadModel.user_id == user_id)
            .where(ChatThreadModel.is_favorite == True)
            .order_by(ChatThreadModel.updated_at.desc())
        )
        
        result = await self.session.execute(stmt)
        db_threads = result.scalars().all()
        
        return [self._model_to_entity(db_thread) for db_thread in db_threads]

    async def get_shared_threads(self, user_id: int) -> List[ChatThreadEntity]:
        """Get threads shared with a user."""
        stmt = (
            select(ChatThreadModel)
            .where(ChatThreadModel.is_shared == True)
            .where(ChatThreadModel.user_id != user_id)  # Not owned by user
            .order_by(ChatThreadModel.updated_at.desc())
        )
        
        result = await self.session.execute(stmt)
        db_threads = result.scalars().all()
        
        # Filter based on sharing permissions
        shared_threads = []
        for db_thread in db_threads:
            thread = self._model_to_entity(db_thread)
            if thread.can_be_accessed_by(user_id):
                shared_threads.append(thread)
                
        return shared_threads

    async def get_thread_hierarchy(self, parent_thread_id: int) -> List[ChatThreadEntity]:
        """Get child threads in hierarchy."""
        stmt = (
            select(ChatThreadModel)
            .where(ChatThreadModel.parent_thread_id == parent_thread_id)
            .order_by(ChatThreadModel.thread_order)
        )
        
        result = await self.session.execute(stmt)
        db_threads = result.scalars().all()
        
        return [self._model_to_entity(db_thread) for db_thread in db_threads]

    async def archive_thread(self, thread_id: int, user_id: int) -> bool:
        """Archive a thread."""
        stmt = (
            update(ChatThreadModel)
            .where(ChatThreadModel.id == thread_id)
            .where(ChatThreadModel.user_id == user_id)
            .values(status=ThreadStatus.ARCHIVED.value, archived_at=datetime.utcnow())
        )
        
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def restore_thread(self, thread_id: int, user_id: int) -> bool:
        """Restore an archived thread."""
        stmt = (
            update(ChatThreadModel)
            .where(ChatThreadModel.id == thread_id)
            .where(ChatThreadModel.user_id == user_id)
            .values(status=ThreadStatus.ACTIVE.value, archived_at=None)
        )
        
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def bulk_update_status(
        self, 
        thread_ids: List[int], 
        user_id: int, 
        status: ThreadStatus
    ) -> int:
        """Bulk update thread status. Returns number of updated threads."""
        stmt = (
            update(ChatThreadModel)
            .where(ChatThreadModel.id.in_(thread_ids))
            .where(ChatThreadModel.user_id == user_id)
            .values(status=status.value, updated_at=datetime.utcnow())
        )
        
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_thread_analytics(
        self, 
        user_id: int, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get thread analytics for a user."""
        stmt = select(ChatThreadModel).where(ChatThreadModel.user_id == user_id)
        
        if start_date:
            stmt = stmt.where(ChatThreadModel.created_at >= start_date)
        if end_date:
            stmt = stmt.where(ChatThreadModel.created_at <= end_date)
            
        result = await self.session.execute(stmt)
        threads = result.scalars().all()
        
        analytics = {
            'total_threads': len(threads),
            'active_threads': sum(1 for t in threads if t.status == ThreadStatus.ACTIVE.value),
            'archived_threads': sum(1 for t in threads if t.status == ThreadStatus.ARCHIVED.value),
            'favorite_threads': sum(1 for t in threads if t.is_favorite),
            'shared_threads': sum(1 for t in threads if t.is_shared),
            'total_messages': sum(t.message_count for t in threads),
            'total_documents': sum(t.document_count for t in threads),
            'total_tokens': sum(t.total_tokens_used for t in threads),
            'categories': {},
        }
        
        # Category breakdown
        for thread in threads:
            cat = thread.category
            analytics['categories'][cat] = analytics['categories'].get(cat, 0) + 1
            
        return analytics

    async def count_by_user_id(self, user_id: int) -> int:
        """Count the number of threads for a user."""
        stmt = select(func.count(ChatThreadModel.id)).where(ChatThreadModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class SQLAChatMessageRepository(ChatMessageRepository):
    """SQLAlchemy implementation of ChatMessageRepository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _model_to_entity(self, db_message: ChatMessageModel) -> ChatMessageEntity:
        """Convert database model to domain entity."""
        from ...domain.entities.chat.chat_entities import MessageRole, MessageType
        
        return ChatMessageEntity(
            id=db_message.id,
            thread_id=db_message.thread_id,
            user_id=db_message.user_id,
            content=db_message.content,
            role=MessageRole(db_message.role),
            message_type=MessageType(db_message.message_type),
            status=MessageStatus(db_message.status),
            original_content=db_message.original_content,
            edit_count=db_message.edit_count,
            version=db_message.version,
            ai_request_id=db_message.ai_request_id,
            ai_model=db_message.ai_model,
            ai_provider=db_message.ai_provider,
            tokens_used=db_message.tokens_used,
            processing_time_ms=db_message.processing_time_ms,
            parent_message_id=db_message.parent_message_id,
            reply_to_message_id=db_message.reply_to_message_id,
            created_at=db_message.created_at,
            updated_at=db_message.updated_at,
            processed_at=db_message.processed_at,
            deleted_at=db_message.deleted_at,
            content_summary=db_message.content_summary,
            sentiment_score=db_message.sentiment_score,
            content_vector=db_message.content_vector,
            meta_data=db_message.meta_data or {},
            ai_metadata=db_message.ai_metadata or {},
            annotations=db_message.annotations or {}
        )
    
    def _entity_to_model_data(self, message: ChatMessageEntity) -> dict:
        """Convert domain entity to model data for database operations."""
        return {
            'thread_id': message.thread_id,
            'user_id': message.user_id,
            'content': message.content,
            'role': message.role,
            'message_type': message.message_type,
            'status': message.status.value,
            'original_content': message.original_content,
            'edit_count': message.edit_count,
            'version': message.version,
            'ai_request_id': message.ai_request_id,
            'ai_model': message.ai_model,
            'ai_provider': message.ai_provider,
            'tokens_used': message.tokens_used,
            'processing_time_ms': message.processing_time_ms,
            'parent_message_id': message.parent_message_id,
            'reply_to_message_id': message.reply_to_message_id,
            'updated_at': message.updated_at or datetime.utcnow(),
            'processed_at': message.processed_at,
            'deleted_at': message.deleted_at,
            'content_summary': message.content_summary,
            'sentiment_score': message.sentiment_score,
            'content_vector': message.content_vector,
            'meta_data': message.meta_data,
            'ai_metadata': message.ai_metadata,
            'annotations': message.annotations
        }

    async def create(self, message: ChatMessageEntity) -> ChatMessageEntity:
        """Create a new chat message."""
        db_message = ChatMessageModel(
            **self._entity_to_model_data(message),
            created_at=datetime.utcnow()
        )
        
        self.session.add(db_message)
        await self.session.flush()
        await self.session.refresh(db_message)
        
        return self._model_to_entity(db_message)

    async def get_by_id(self, message_id: int) -> Optional[ChatMessageEntity]:
        """Get a chat message by ID."""
        stmt = select(ChatMessageModel).where(ChatMessageModel.id == message_id)
        result = await self.session.execute(stmt)
        db_message = result.scalar_one_or_none()
        
        return self._model_to_entity(db_message) if db_message else None

    async def update(self, message: ChatMessageEntity) -> ChatMessageEntity:
        """Update a chat message."""
        if not message.id:
            raise ValueError("Cannot update message without ID")
            
        stmt = (
            update(ChatMessageModel)
            .where(ChatMessageModel.id == message.id)
            .values(**self._entity_to_model_data(message))
        )
        
        await self.session.execute(stmt)
        updated_message = await self.get_by_id(message.id)
        if updated_message is None:
            raise ValueError(f"Message with ID {message.id} not found after update")
        return updated_message

    async def delete(self, message_id: int) -> bool:
        """Delete a chat message."""
        stmt = (
            update(ChatMessageModel)
            .where(ChatMessageModel.id == message_id)
            .values(deleted_at=datetime.utcnow())
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_by_thread(
        self, 
        thread_id: int, 
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[ChatMessageEntity]:
        """Get messages for a thread with pagination."""
        stmt = select(ChatMessageModel).where(ChatMessageModel.thread_id == thread_id)
        
        if not include_deleted:
            stmt = stmt.where(ChatMessageModel.deleted_at.is_(None))
            
        stmt = stmt.offset(offset).limit(limit).order_by(ChatMessageModel.created_at)
        
        result = await self.session.execute(stmt)
        db_messages = result.scalars().all()
        
        return [self._model_to_entity(db_message) for db_message in db_messages]

    async def get_by_user(self, user_id: int, limit: int = 50) -> List[ChatMessageEntity]:
        """Get recent messages by user."""
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.user_id == user_id)
            .where(ChatMessageModel.deleted_at.is_(None))
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        db_messages = result.scalars().all()
        
        return [self._model_to_entity(db_message) for db_message in db_messages]

    async def search_messages(
        self, 
        thread_id: int, 
        query: str,
        limit: int = 20
    ) -> List[ChatMessageEntity]:
        """Search messages within a thread."""
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.thread_id == thread_id)
            .where(ChatMessageModel.content.ilike(f"%{query}%"))
            .where(ChatMessageModel.deleted_at.is_(None))
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        db_messages = result.scalars().all()
        
        return [self._model_to_entity(db_message) for db_message in db_messages]

    async def get_ai_messages(
        self, 
        thread_id: int,
        ai_provider: Optional[str] = None,
        limit: int = 50
    ) -> List[ChatMessageEntity]:
        """Get AI-generated messages."""
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.thread_id == thread_id)
            .where(ChatMessageModel.role == "assistant")
            .where(ChatMessageModel.deleted_at.is_(None))
        )
        
        if ai_provider:
            stmt = stmt.where(ChatMessageModel.ai_provider == ai_provider)
            
        stmt = stmt.order_by(ChatMessageModel.created_at.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        db_messages = result.scalars().all()
        
        return [self._model_to_entity(db_message) for db_message in db_messages]

    async def get_message_thread(self, message_id: int) -> List[ChatMessageEntity]:
        """Get message thread (parent and children)."""
        # This is a simplified implementation - would need recursive CTE for full thread
        stmt = (
            select(ChatMessageModel)
            .where(
                (ChatMessageModel.id == message_id) |
                (ChatMessageModel.parent_message_id == message_id) |
                (ChatMessageModel.reply_to_message_id == message_id)
            )
            .order_by(ChatMessageModel.created_at)
        )
        
        result = await self.session.execute(stmt)
        db_messages = result.scalars().all()
        
        return [self._model_to_entity(db_message) for db_message in db_messages]

    async def get_conversation_context(
        self, 
        thread_id: int, 
        max_tokens: int = 4000
    ) -> List[ChatMessageEntity]:
        """Get conversation context within token limit."""
        # Get recent messages in reverse order
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.thread_id == thread_id)
            .where(ChatMessageModel.deleted_at.is_(None))
            .order_by(ChatMessageModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        db_messages = result.scalars().all()
        
        # Calculate tokens and return context
        context_messages = []
        total_tokens = 0
        
        for db_message in db_messages:
            message_tokens = db_message.tokens_used or len(db_message.content) // 4  # Rough estimate
            if total_tokens + message_tokens > max_tokens and context_messages:
                break
            context_messages.append(self._model_to_entity(db_message))
            total_tokens += message_tokens
        
        # Return in chronological order
        return list(reversed(context_messages))

    async def update_message_status(
        self, 
        message_id: int, 
        status: MessageStatus
    ) -> bool:
        """Update message status."""
        stmt = (
            update(ChatMessageModel)
            .where(ChatMessageModel.id == message_id)
            .values(status=status.value, updated_at=datetime.utcnow())
        )
        
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_processing_messages(self) -> List[ChatMessageEntity]:
        """Get messages currently being processed."""
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.status == MessageStatus.PROCESSING.value)
            .order_by(ChatMessageModel.created_at)
        )
        
        result = await self.session.execute(stmt)
        db_messages = result.scalars().all()
        
        return [self._model_to_entity(db_message) for db_message in db_messages]


class SQLADocumentRepository(DocumentRepository):
    """SQLAlchemy implementation of DocumentRepository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _model_to_entity(self, db_document: DocumentModel) -> DocumentEntity:
        """Convert database model to domain entity."""
        from ...domain.entities.chat.chat_entities import DocumentType
        
        # Map database document_type to enum
        try:
            doc_type = DocumentType(db_document.document_type)
        except ValueError:
            doc_type = DocumentType.TXT  # Default fallback
        
        return DocumentEntity(
            id=db_document.id,
            thread_id=db_document.thread_id,
            user_id=db_document.user_id,
            filename=db_document.filename,
            original_filename=db_document.original_filename,
            mime_type=db_document.mime_type,
            file_extension=db_document.file_extension,
            size_bytes=db_document.size_bytes,
            document_type=doc_type,
            storage_path=db_document.storage_path,
            processing_status=ProcessingStatus(db_document.processing_status),
            content_hash=db_document.content_hash,
            extracted_text=db_document.extracted_text,
            chunk_count=db_document.chunk_count,
            vector_store_id=db_document.vector_store_id,
            processing_error=db_document.processing_error,
            created_at=db_document.created_at,
            updated_at=db_document.updated_at,
            processing_completed_at=db_document.processing_completed_at,
            meta_data=db_document.meta_data or {},
            processing_metadata=db_document.processing_metadata or {}
        )
    
    def _entity_to_model_data(self, document: DocumentEntity) -> dict:
        """Convert domain entity to model data for database operations."""
        return {
            'thread_id': document.thread_id,
            'user_id': document.user_id,
            'filename': document.filename,
            'original_filename': document.original_filename,
            'mime_type': document.mime_type,
            'file_extension': document.file_extension,
            'size_bytes': document.size_bytes,
            'document_type': document.document_type.value,
            'storage_path': document.storage_path,
            'processing_status': document.processing_status.value,
            'content_hash': document.content_hash,
            'extracted_text': document.extracted_text,
            'chunk_count': document.chunk_count,
            'vector_store_id': document.vector_store_id,
            'processing_error': document.processing_error,
            'updated_at': document.updated_at or datetime.utcnow(),
            'processing_completed_at': document.processing_completed_at,
            'meta_data': document.meta_data,
            'processing_metadata': document.processing_metadata
        }

    async def create(self, document: DocumentEntity) -> DocumentEntity:
        """Create a new document."""
        db_document = DocumentModel(
            **self._entity_to_model_data(document),
            created_at=datetime.utcnow()
        )
        
        self.session.add(db_document)
        await self.session.flush()
        await self.session.refresh(db_document)
        
        return self._model_to_entity(db_document)

    async def get_by_id(self, document_id: int) -> Optional[DocumentEntity]:
        """Get a document by ID."""
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self.session.execute(stmt)
        db_document = result.scalar_one_or_none()
        
        return self._model_to_entity(db_document) if db_document else None

    async def update(self, document: DocumentEntity) -> DocumentEntity:
        """Update a document."""
        if not document.id:
            raise ValueError("Cannot update document without ID")
            
        stmt = (
            update(DocumentModel)
            .where(DocumentModel.id == document.id)
            .values(**self._entity_to_model_data(document))
        )
        
        await self.session.execute(stmt)
        updated_document = await self.get_by_id(document.id)
        if updated_document is None:
            raise ValueError(f"Document with ID {document.id} not found after update")
        return updated_document

    async def delete(self, document_id: int) -> bool:
        """Delete a document."""
        stmt = delete(DocumentModel).where(DocumentModel.id == document_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_by_thread(self, thread_id: int) -> List[DocumentEntity]:
        """Get all documents for a thread."""
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.thread_id == thread_id)
            .order_by(DocumentModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        db_documents = result.scalars().all()
        
        return [self._model_to_entity(db_document) for db_document in db_documents]

    async def get_by_user(
        self, 
        user_id: int, 
        processing_status: Optional[ProcessingStatus] = None
    ) -> List[DocumentEntity]:
        """Get documents by user with optional status filter."""
        stmt = select(DocumentModel).where(DocumentModel.user_id == user_id)
        
        if processing_status:
            stmt = stmt.where(DocumentModel.processing_status == processing_status.value)
            
        stmt = stmt.order_by(DocumentModel.created_at.desc())
        
        result = await self.session.execute(stmt)
        db_documents = result.scalars().all()
        
        return [self._model_to_entity(db_document) for db_document in db_documents]

    async def get_by_hash(self, content_hash: str) -> Optional[DocumentEntity]:
        """Get document by content hash (duplicate detection)."""
        stmt = select(DocumentModel).where(DocumentModel.content_hash == content_hash)
        result = await self.session.execute(stmt)
        db_document = result.scalar_one_or_none()
        
        return self._model_to_entity(db_document) if db_document else None

    async def search_documents(
        self, 
        user_id: int, 
        query: str,
        document_types: Optional[List[str]] = None
    ) -> List[DocumentEntity]:
        """Search documents by content or metadata."""
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.user_id == user_id)
            .where(
                DocumentModel.filename.ilike(f"%{query}%") |
                DocumentModel.extracted_text.ilike(f"%{query}%")
            )
        )
        
        if document_types:
            stmt = stmt.where(DocumentModel.document_type.in_(document_types))
            
        stmt = stmt.order_by(DocumentModel.created_at.desc())
        
        result = await self.session.execute(stmt)
        db_documents = result.scalars().all()
        
        return [self._model_to_entity(db_document) for db_document in db_documents]

    async def get_processing_queue(self, limit: int = 10) -> List[DocumentEntity]:
        """Get documents pending processing."""
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.processing_status == ProcessingStatus.PENDING.value)
            .order_by(DocumentModel.created_at)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        db_documents = result.scalars().all()
        
        return [self._model_to_entity(db_document) for db_document in db_documents]

    async def get_failed_processing(self) -> List[DocumentEntity]:
        """Get documents with failed processing."""
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.processing_status == ProcessingStatus.FAILED.value)
            .order_by(DocumentModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        db_documents = result.scalars().all()
        
        return [self._model_to_entity(db_document) for db_document in db_documents]

    async def update_processing_status(
        self, 
        document_id: int, 
        status: ProcessingStatus,
        error: Optional[str] = None
    ) -> bool:
        """Update document processing status."""
        update_data = {
            'processing_status': status.value,
            'updated_at': datetime.utcnow()
        }
        
        if status == ProcessingStatus.COMPLETED:
            update_data['processed_at'] = datetime.utcnow()
        elif status == ProcessingStatus.FAILED and error:
            update_data['processing_error'] = error
            
        stmt = (
            update(DocumentModel)
            .where(DocumentModel.id == document_id)
            .values(**update_data)
        )
        
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_searchable_documents(self, thread_id: int) -> List[DocumentEntity]:
        """Get documents ready for semantic search."""
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.thread_id == thread_id)
            .where(DocumentModel.processing_status == ProcessingStatus.COMPLETED.value)
            .where(DocumentModel.vector_store_id.is_not(None))
            .order_by(DocumentModel.processing_completed_at.desc())
        )
        
        result = await self.session.execute(stmt)
        db_documents = result.scalars().all()
        
        return [self._model_to_entity(db_document) for db_document in db_documents]