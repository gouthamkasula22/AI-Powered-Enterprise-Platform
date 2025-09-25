"""
Enhanced Chat Domain Entities

This module contains the enhanced domain entities for the chat system
with advanced thread management, message processing, and document handling capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ReactionType(Enum):
    """Types of message reactions."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    HEART = "heart"
    LAUGH = "laugh"
    SURPRISED = "surprised"
    ANGRY = "angry"
    CONFUSED = "confused"
    CUSTOM = "custom"


class EditType(Enum):
    """Types of message edits."""
    CONTENT = "content"
    FORMATTING = "formatting"
    CORRECTION = "correction"
    ENHANCEMENT = "enhancement"
    SYSTEM = "system"


class ProcessingStage(Enum):
    """AI message processing stages."""
    RECEIVED = "received"
    QUEUED = "queued"
    PREPROCESSING = "preprocessing"
    AI_PROCESSING = "ai_processing"
    POSTPROCESSING = "postprocessing"
    COMPLETED = "completed"
    FAILED = "failed"


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


@dataclass(frozen=True)
class ChatThread:
    """
    Enhanced Chat Thread domain entity with advanced management features.
    
    This entity represents a conversation thread with support for:
    - Hierarchical organization
    - Categorization and tagging
    - Access control and sharing
    - Analytics and statistics
    - AI configuration
    """
    
    # Primary identifiers
    id: Optional[int] = None
    user_id: int = 0
    
    # Basic thread information
    title: str = ""
    status: ThreadStatus = ThreadStatus.ACTIVE
    category: ThreadCategory = ThreadCategory.GENERAL
    tags: Optional[List[str]] = None
    
    # Thread management flags
    is_favorite: bool = False
    is_shared: bool = False
    
    # Hierarchy support
    parent_thread_id: Optional[int] = None
    thread_order: int = 0
    children: List['ChatThread'] = field(default_factory=list)
    
    # Access control
    sharing_permissions: Dict[str, Any] = field(default_factory=dict)
    access_level: str = "private"
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    
    # Statistics and analytics
    message_count: int = 0
    document_count: int = 0
    total_tokens_used: int = 0
    
    # Associated entities
    messages: List['ChatMessage'] = field(default_factory=list)
    documents: List['Document'] = field(default_factory=list)
    
    # Configuration and metadata
    meta_data: Dict[str, Any] = field(default_factory=dict)
    ai_configuration: Dict[str, Any] = field(default_factory=dict)
    
    def is_archived(self) -> bool:
        """Check if thread is archived."""
        return self.status == ThreadStatus.ARCHIVED
    
    def is_active(self) -> bool:
        """Check if thread is active."""
        return self.status == ThreadStatus.ACTIVE
    
    def can_be_accessed_by(self, user_id: int) -> bool:
        """Check if user can access this thread."""
        if self.user_id == user_id:
            return True
        
        if self.access_level == "public":
            return True
            
        # Check sharing permissions
        return user_id in self.sharing_permissions.get("users", [])
    
    def add_tag(self, tag: str) -> 'ChatThread':
        """Add a tag to the thread and return new instance."""
        tags = list(self.tags) if self.tags else []
        if tag not in tags:
            tags.append(tag)
            return self.__class__(
                id=self.id,
                user_id=self.user_id,
                title=self.title,
                status=self.status,
                category=self.category,
                tags=tags,
                is_favorite=self.is_favorite,
                is_shared=self.is_shared,
                parent_thread_id=self.parent_thread_id,
                thread_order=self.thread_order,
                children=self.children,
                sharing_permissions=self.sharing_permissions,
                access_level=self.access_level,
                created_at=self.created_at,
                updated_at=self.updated_at,
                last_message_at=self.last_message_at,
                archived_at=self.archived_at,
                message_count=self.message_count,
                document_count=self.document_count,
                total_tokens_used=self.total_tokens_used,
                messages=self.messages,
                documents=self.documents,
                meta_data=self.meta_data,
                ai_configuration=self.ai_configuration
            )
        return self
    
    def remove_tag(self, tag: str) -> 'ChatThread':
        """Remove a tag from the thread and return new instance."""
        if not self.tags or tag not in self.tags:
            return self
            
        tags = [t for t in self.tags if t != tag]
        return self.__class__(
            id=self.id,
            user_id=self.user_id,
            title=self.title,
            status=self.status,
            category=self.category,
            tags=tags,
            is_favorite=self.is_favorite,
            is_shared=self.is_shared,
            parent_thread_id=self.parent_thread_id,
            thread_order=self.thread_order,
            children=self.children,
            sharing_permissions=self.sharing_permissions,
            access_level=self.access_level,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_message_at=self.last_message_at,
            archived_at=self.archived_at,
            message_count=self.message_count,
            document_count=self.document_count,
            total_tokens_used=self.total_tokens_used,
            messages=self.messages,
            documents=self.documents,
            meta_data=self.meta_data,
            ai_configuration=self.ai_configuration
        )


@dataclass(frozen=True)
class ChatMessage:
    """
    Enhanced Chat Message domain entity with advanced features.
    
    This entity represents a message with support for:
    - Message versioning and editing
    - AI-powered responses
    - Message threading and relationships
    - Content analysis and embeddings
    - Rich metadata and annotations
    """
    
    # Primary identifiers
    id: Optional[int] = None
    thread_id: int = 0
    user_id: int = 0
    
    # Message content
    content: str = ""
    role: MessageRole = MessageRole.USER
    message_type: MessageType = MessageType.TEXT
    status: MessageStatus = MessageStatus.PENDING
    
    # Message versioning
    original_content: Optional[str] = None
    edit_count: int = 0
    version: int = 1
    
    # AI-specific fields
    ai_request_id: Optional[str] = None
    ai_model: Optional[str] = None
    ai_provider: Optional[str] = None
    tokens_used: int = 0
    processing_time_ms: int = 0
    
    # Message relationships
    parent_message_id: Optional[int] = None
    reply_to_message_id: Optional[int] = None
    children: List['ChatMessage'] = field(default_factory=list)
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    # Content analysis
    content_summary: Optional[str] = None
    sentiment_score: Optional[float] = None
    content_vector: Optional[str] = None  # Embedding reference
    
    # Metadata and annotations
    meta_data: Dict[str, Any] = field(default_factory=dict)
    ai_metadata: Dict[str, Any] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)
    
    def is_ai_response(self) -> bool:
        """Check if this is an AI-generated response."""
        return self.role == MessageRole.ASSISTANT or self.message_type == MessageType.AI_RESPONSE
    
    def is_user_message(self) -> bool:
        """Check if this is a user message."""
        return self.role == MessageRole.USER
    
    def is_edited(self) -> bool:
        """Check if message has been edited."""
        return self.edit_count > 0
    
    def is_processing(self) -> bool:
        """Check if message is currently being processed."""
        return self.status == MessageStatus.PROCESSING
    
    def has_ai_metadata(self) -> bool:
        """Check if message has AI-related metadata."""
        return bool(self.ai_metadata or self.ai_request_id)


@dataclass(frozen=True)
class Document:
    """
    Enhanced Document domain entity with advanced processing capabilities.
    
    This entity represents a document with support for:
    - Multi-format processing
    - Security scanning and validation
    - Vector embeddings and search
    - Content analysis and extraction
    - Access control and sharing
    """
    
    # Primary identifiers
    id: Optional[int] = None
    thread_id: int = 0
    user_id: int = 0
    
    # File information
    filename: str = ""
    original_filename: str = ""
    mime_type: str = ""
    file_extension: str = ""
    size_bytes: int = 0
    document_type: DocumentType = DocumentType.TXT
    
    # Security and validation
    content_hash: str = ""
    checksum: str = ""
    virus_scan_status: str = "pending"
    virus_scan_result: Optional[str] = None
    
    # Processing information
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_error: Optional[str] = None
    processing_attempts: int = 0
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    
    # Content extraction
    extracted_text: Optional[str] = None
    extracted_metadata: Dict[str, Any] = field(default_factory=dict)
    content_summary: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    
    # Vector embeddings
    chunk_count: int = 0
    embedding_model: Optional[str] = None
    embedding_status: str = "pending"
    vector_store_id: Optional[str] = None
    chunks: List['DocumentChunk'] = field(default_factory=list)
    
    # Access control
    is_public: bool = False
    access_permissions: Dict[str, Any] = field(default_factory=dict)
    sharing_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Storage information
    storage_path: str = ""
    storage_provider: str = "local"
    backup_status: str = "pending"
    
    # Analytics
    download_count: int = 0
    view_count: int = 0
    search_count: int = 0
    last_accessed_at: Optional[datetime] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    # Metadata
    meta_data: Dict[str, Any] = field(default_factory=dict)
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    
    def is_processed(self) -> bool:
        """Check if document has been processed successfully."""
        return self.processing_status == ProcessingStatus.COMPLETED
    
    def is_processing(self) -> bool:
        """Check if document is currently being processed."""
        return self.processing_status == ProcessingStatus.PROCESSING
    
    def has_failed_processing(self) -> bool:
        """Check if document processing has failed."""
        return self.processing_status == ProcessingStatus.FAILED
    
    def is_searchable(self) -> bool:
        """Check if document is ready for search."""
        return (self.is_processed() and 
                self.embedding_status == "completed" and 
                self.chunk_count > 0)
    
    def can_be_accessed_by(self, user_id: int) -> bool:
        """Check if user can access this document."""
        if self.user_id == user_id:
            return True
        
        if self.is_public:
            return True
            
        return user_id in self.access_permissions.get("users", [])
    
    def get_file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.size_bytes / (1024 * 1024)


@dataclass(frozen=True)
class DocumentChunk:
    """
    Document Chunk domain entity for vector search.
    
    This entity represents a processed chunk of a document
    that can be used for semantic search and retrieval.
    """
    
    # Primary identifiers
    id: Optional[int] = None
    document_id: int = 0
    
    # Chunk information
    chunk_index: int = 0
    content: str = ""
    content_hash: str = ""
    
    # Position information
    start_position: int = 0
    end_position: int = 0
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    
    # Vector embedding
    embedding_vector: Optional[str] = None  # JSON serialized vector
    embedding_model: Optional[str] = None
    vector_store_id: Optional[str] = None
    
    # Content statistics
    token_count: int = 0
    character_count: int = 0
    word_count: int = 0
    
    # Quality metrics
    quality_score: Optional[float] = None
    relevance_score: Optional[float] = None
    importance_score: Optional[float] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Metadata
    chunk_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_embedded(self) -> bool:
        """Check if chunk has been embedded."""
        return bool(self.embedding_vector and self.vector_store_id)
    
    def get_content_preview(self, max_chars: int = 100) -> str:
        """Get a preview of the content."""
        if len(self.content) <= max_chars:
            return self.content
        return self.content[:max_chars] + "..."
    
    def calculate_density_score(self) -> float:
        """Calculate content density score."""
        if self.character_count == 0:
            return 0.0
        return self.word_count / self.character_count
