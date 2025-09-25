"""
Chat Database Models

This module defines the SQLAlchemy models for chat entities.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, BigInteger, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from ..config import Base

if TYPE_CHECKING:
    from .message_processing_models import MessageReaction, MessageEdit, MessageVersion, AIProcessingStep, MessageSearchIndex


class ThreadStatus(Enum):
    """Enum for chat thread status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PINNED = "pinned"


class ThreadCategory(Enum):
    """Enum for chat thread categories."""
    GENERAL = "general"
    WORK = "work"
    PERSONAL = "personal"
    RESEARCH = "research"
    SUPPORT = "support"
    PROJECT = "project"


class ChatThread(Base):
    """SQLAlchemy model for a chat thread with advanced management features."""
    __tablename__ = "chat_threads"
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Enhanced thread management fields
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ThreadStatus.ACTIVE.value)
    category: Mapped[str] = mapped_column(String(20), nullable=False, default=ThreadCategory.GENERAL.value)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Hierarchy support
    parent_thread_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chat_threads.id"), nullable=True)
    thread_order: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    # Access control
    sharing_permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    access_level: Mapped[str] = mapped_column(String(20), nullable=False, default="private")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Statistics and analytics
    message_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    document_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    total_tokens_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    # Extended metadata
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    ai_configuration: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="thread", cascade="all, delete-orphan")
    
    # Self-referential relationship for thread hierarchy
    children: Mapped[List["ChatThread"]] = relationship("ChatThread", back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped[Optional["ChatThread"]] = relationship("ChatThread", back_populates="children", remote_side=[id])
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_chat_threads_user_status', 'user_id', 'status'),
        Index('idx_chat_threads_category', 'category'),
        Index('idx_chat_threads_updated_at', 'updated_at'),
        Index('idx_chat_threads_last_message', 'last_message_at'),
        Index('idx_chat_threads_hierarchy', 'parent_thread_id', 'thread_order'),
    )


class MessageRole(Enum):
    """Enum for message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


class MessageStatus(Enum):
    """Enum for message processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EDITED = "edited"
    DELETED = "deleted"


class MessageType(Enum):
    """Enum for message types."""
    TEXT = "text"
    AI_RESPONSE = "ai_response"
    SYSTEM_NOTIFICATION = "system_notification"
    FILE_UPLOAD = "file_upload"
    FUNCTION_CALL = "function_call"


class ChatMessage(Base):
    """SQLAlchemy model for a chat message with enhanced features."""
    __tablename__ = "chat_messages"
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Message content and metadata
    content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=MessageRole.USER.value)
    message_type: Mapped[str] = mapped_column(String(30), nullable=False, default=MessageType.TEXT.value)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=MessageStatus.PENDING.value)
    
    # Message versioning and editing
    original_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edit_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    
    # AI-specific fields
    ai_request_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tokens_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    processing_time_ms: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    # Message relationships and references
    parent_message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chat_messages.id"), nullable=True)
    reply_to_message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chat_messages.id"), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Content analysis and search
    content_summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    content_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Embedding reference
    
    # Extended metadata
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    ai_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    annotations: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    thread: Mapped["ChatThread"] = relationship("ChatThread", back_populates="messages")
    
    # Self-referential relationships for message threading
    children: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="parent", foreign_keys=[parent_message_id])
    parent: Mapped[Optional["ChatMessage"]] = relationship("ChatMessage", back_populates="children", remote_side=[id], foreign_keys=[parent_message_id])
    
    # Enhanced message processing relationships
    reactions: Mapped[List["MessageReaction"]] = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan")
    edits: Mapped[List["MessageEdit"]] = relationship("MessageEdit", back_populates="message", cascade="all, delete-orphan")
    versions: Mapped[List["MessageVersion"]] = relationship("MessageVersion", back_populates="message", cascade="all, delete-orphan")
    processing_steps: Mapped[List["AIProcessingStep"]] = relationship("AIProcessingStep", back_populates="message", cascade="all, delete-orphan")
    search_index: Mapped[Optional["MessageSearchIndex"]] = relationship("MessageSearchIndex", back_populates="message", cascade="all, delete-orphan", uselist=False)
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_chat_messages_thread_created', 'thread_id', 'created_at'),
        Index('idx_chat_messages_user_thread', 'user_id', 'thread_id'),
        Index('idx_chat_messages_status', 'status'),
        Index('idx_chat_messages_type_role', 'message_type', 'role'),
        Index('idx_chat_messages_ai_request', 'ai_request_id'),
        Index('idx_chat_messages_parent', 'parent_message_id'),
    )


class DocumentType(Enum):
    """Enum for document types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    IMAGE = "image"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"


class ProcessingStatus(Enum):
    """Enum for document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class Document(Base):
    """SQLAlchemy model for a document with advanced processing capabilities."""
    __tablename__ = "chat_documents"
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Security and validation
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    virus_scan_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    virus_scan_result: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Processing status and metadata
    processing_status: Mapped[str] = mapped_column(String(20), nullable=False, default=ProcessingStatus.PENDING.value)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_attempts: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Content extraction
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    content_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    character_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Vector embeddings and search
    chunk_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    vector_store_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Access control and sharing
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    access_permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    sharing_settings: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Storage information
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    backup_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    
    # Analytics and usage
    download_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    search_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Extended metadata
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    processing_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    analysis_results: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    thread: Mapped["ChatThread"] = relationship("ChatThread", back_populates="documents")
    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_chat_documents_thread', 'thread_id'),
        Index('idx_chat_documents_user', 'user_id'),
        Index('idx_chat_documents_status', 'processing_status'),
        Index('idx_chat_documents_type', 'document_type'),
        Index('idx_chat_documents_hash', 'content_hash'),
        Index('idx_chat_documents_created', 'created_at'),
        Index('idx_chat_documents_embedding', 'embedding_status'),
    )


class DocumentChunk(Base):
    """SQLAlchemy model for document chunks used in vector search."""
    __tablename__ = "document_chunks"
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("chat_documents.id", ondelete="CASCADE"), nullable=False)
    
    # Chunk information
    chunk_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Chunk metadata
    start_position: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    end_position: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    page_number: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Vector embedding information
    embedding_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON serialized vector
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vector_store_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Content analysis
    token_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    character_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    word_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    # Quality and relevance metrics
    quality_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    importance_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Extended metadata
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_document_chunks_document', 'document_id'),
        Index('idx_document_chunks_index', 'chunk_index'),
        Index('idx_document_chunks_hash', 'content_hash'),
        Index('idx_document_chunks_vector_store', 'vector_store_id'),
        Index('idx_document_chunks_page', 'page_number'),
    )