"""
Enhanced Chat Repository Interfaces

This module defines the enhanced repository interfaces for the chat domain
with support for advanced thread management, message processing, and document handling.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from ..entities.chat.chat_entities import (
    ChatThread, ChatMessage, Document, DocumentChunk,
    ThreadStatus, ThreadCategory, MessageStatus, ProcessingStatus
)


class ChatThreadRepository(ABC):
    """Enhanced repository interface for ChatThread entities."""
    
    # Basic CRUD operations
    @abstractmethod
    async def create(self, thread: ChatThread) -> ChatThread:
        """Create a new chat thread."""
        pass
    
    @abstractmethod
    async def get_by_id(self, thread_id: int) -> Optional[ChatThread]:
        """Get a chat thread by ID."""
        pass
    
    @abstractmethod
    async def update(self, thread: ChatThread) -> ChatThread:
        """Update an existing chat thread."""
        pass
    
    @abstractmethod
    async def delete(self, thread_id: int) -> bool:
        """Delete a chat thread."""
        pass
    
    # Enhanced query methods
    @abstractmethod
    async def get_by_user(
        self, 
        user_id: int, 
        status: Optional[ThreadStatus] = None,
        category: Optional[ThreadCategory] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatThread]:
        """Get chat threads for a user with filtering options."""
        pass
    
    @abstractmethod
    async def get_by_user_with_stats(self, user_id: int) -> List[Tuple[ChatThread, Dict[str, Any]]]:
        """Get chat threads for a user with statistics."""
        pass
    
    @abstractmethod
    async def search_threads(
        self, 
        user_id: int, 
        query: str,
        categories: Optional[List[ThreadCategory]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[ChatThread]:
        """Search chat threads by content, title, or tags."""
        pass
    
    @abstractmethod
    async def get_favorites(self, user_id: int) -> List[ChatThread]:
        """Get favorite threads for a user."""
        pass
    
    @abstractmethod
    async def get_shared_threads(self, user_id: int) -> List[ChatThread]:
        """Get threads shared with a user."""
        pass
    
    @abstractmethod
    async def get_thread_hierarchy(self, parent_thread_id: int) -> List[ChatThread]:
        """Get child threads in hierarchy."""
        pass
    
    @abstractmethod
    async def archive_thread(self, thread_id: int, user_id: int) -> bool:
        """Archive a thread."""
        pass
    
    @abstractmethod
    async def restore_thread(self, thread_id: int, user_id: int) -> bool:
        """Restore an archived thread."""
        pass
    
    @abstractmethod
    async def bulk_update_status(
        self, 
        thread_ids: List[int], 
        user_id: int, 
        status: ThreadStatus
    ) -> int:
        """Bulk update thread status. Returns number of updated threads."""
        pass
    
    @abstractmethod
    async def get_thread_analytics(
        self, 
        user_id: int, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get thread analytics for a user."""
        pass
    
    @abstractmethod
    async def count_by_user_id(self, user_id: int) -> int:
        """Count the number of threads for a user."""
        pass


class ChatMessageRepository(ABC):
    """Enhanced repository interface for ChatMessage entities."""
    
    # Basic CRUD operations
    @abstractmethod
    async def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new chat message."""
        pass
    
    @abstractmethod
    async def get_by_id(self, message_id: int) -> Optional[ChatMessage]:
        """Get a chat message by ID."""
        pass
    
    @abstractmethod
    async def update(self, message: ChatMessage) -> ChatMessage:
        """Update a chat message."""
        pass
    
    @abstractmethod
    async def delete(self, message_id: int) -> bool:
        """Delete a chat message."""
        pass
    
    # Enhanced query methods
    @abstractmethod
    async def get_by_thread(
        self, 
        thread_id: int, 
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[ChatMessage]:
        """Get messages for a thread with pagination."""
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: int, limit: int = 50) -> List[ChatMessage]:
        """Get recent messages by user."""
        pass
    
    @abstractmethod
    async def search_messages(
        self, 
        thread_id: int, 
        query: str,
        limit: int = 20
    ) -> List[ChatMessage]:
        """Search messages within a thread."""
        pass
    
    @abstractmethod
    async def get_ai_messages(
        self, 
        thread_id: int,
        ai_provider: Optional[str] = None,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get AI-generated messages."""
        pass
    
    @abstractmethod
    async def get_message_thread(self, message_id: int) -> List[ChatMessage]:
        """Get message thread (parent and children)."""
        pass
    
    @abstractmethod
    async def get_conversation_context(
        self, 
        thread_id: int, 
        max_tokens: int = 4000
    ) -> List[ChatMessage]:
        """Get conversation context within token limit."""
        pass
    
    @abstractmethod
    async def update_message_status(
        self, 
        message_id: int, 
        status: MessageStatus
    ) -> bool:
        """Update message status."""
        pass
    
    @abstractmethod
    async def get_processing_messages(self) -> List[ChatMessage]:
        """Get messages currently being processed."""
        pass


class DocumentRepository(ABC):
    """Enhanced repository interface for Document entities."""
    
    # Basic CRUD operations
    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Create a new document."""
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: int) -> Optional[Document]:
        """Get a document by ID."""
        pass
    
    @abstractmethod
    async def update(self, document: Document) -> Document:
        """Update a document."""
        pass
    
    @abstractmethod
    async def delete(self, document_id: int) -> bool:
        """Delete a document."""
        pass
    
    # Enhanced query methods
    @abstractmethod
    async def get_by_thread(self, thread_id: int) -> List[Document]:
        """Get all documents for a thread."""
        pass
    
    @abstractmethod
    async def get_by_user(
        self, 
        user_id: int, 
        processing_status: Optional[ProcessingStatus] = None
    ) -> List[Document]:
        """Get documents by user with optional status filter."""
        pass
    
    @abstractmethod
    async def get_by_hash(self, content_hash: str) -> Optional[Document]:
        """Get document by content hash (duplicate detection)."""
        pass
    
    @abstractmethod
    async def search_documents(
        self, 
        user_id: int, 
        query: str,
        document_types: Optional[List[str]] = None
    ) -> List[Document]:
        """Search documents by content or metadata."""
        pass
    
    @abstractmethod
    async def get_processing_queue(self, limit: int = 10) -> List[Document]:
        """Get documents pending processing."""
        pass
    
    @abstractmethod
    async def get_failed_processing(self) -> List[Document]:
        """Get documents with failed processing."""
        pass
    
    @abstractmethod
    async def update_processing_status(
        self, 
        document_id: int, 
        status: ProcessingStatus,
        error: Optional[str] = None
    ) -> bool:
        """Update document processing status."""
        pass
    
    @abstractmethod
    async def get_searchable_documents(self, thread_id: int) -> List[Document]:
        """Get documents ready for semantic search."""
        pass


class DocumentChunkRepository(ABC):
    """Repository interface for DocumentChunk entities."""
    
    @abstractmethod
    async def create(self, chunk: DocumentChunk) -> DocumentChunk:
        """Create a new document chunk."""
        pass
    
    @abstractmethod
    async def create_bulk(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Create multiple document chunks."""
        pass
    
    @abstractmethod
    async def get_by_document(self, document_id: int) -> List[DocumentChunk]:
        """Get all chunks for a document."""
        pass
    
    @abstractmethod
    async def get_by_vector_store_id(self, vector_store_id: str) -> Optional[DocumentChunk]:
        """Get chunk by vector store ID."""
        pass
    
    @abstractmethod
    async def search_similar(
        self, 
        query_vector: str, 
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar chunks by vector similarity."""
        pass
    
    @abstractmethod
    async def update_embedding(
        self, 
        chunk_id: int, 
        embedding_vector: str,
        vector_store_id: str
    ) -> bool:
        """Update chunk embedding information."""
        pass
    
    @abstractmethod
    async def delete_by_document(self, document_id: int) -> int:
        """Delete all chunks for a document. Returns count of deleted chunks."""
        pass
