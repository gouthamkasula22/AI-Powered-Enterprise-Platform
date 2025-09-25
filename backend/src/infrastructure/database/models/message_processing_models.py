"""
Enhanced Message Processing Database Models

This module defines database models for advanced message processing features
including reactions, editing, version history, and search indexing.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, BigInteger, Boolean, Index, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from enum import Enum

from ..config import Base

if TYPE_CHECKING:
    from .chat_models import ChatMessage
    from .user_model import UserModel


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


class MessageReaction(Base):
    """Model for message reactions."""
    __tablename__ = "message_reactions"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Reaction data
    reaction_type: Mapped[str] = mapped_column(String(50))
    custom_emoji: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="reactions")
    user = relationship("UserModel")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_message_reactions_message_id", "message_id"),
        Index("idx_message_reactions_user_id", "user_id"),
        Index("idx_message_reactions_type", "reaction_type"),
        Index("idx_message_reactions_composite", "message_id", "user_id", "reaction_type"),
    )


class MessageEdit(Base):
    """Model for message edit history."""
    __tablename__ = "message_edits"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Edit data
    edit_type: Mapped[str] = mapped_column(String(50))
    old_content: Mapped[str] = mapped_column(Text)
    new_content: Mapped[str] = mapped_column(Text)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="edits")
    user = relationship("UserModel")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_message_edits_message_id", "message_id"),
        Index("idx_message_edits_user_id", "user_id"),
        Index("idx_message_edits_type", "edit_type"),
        Index("idx_message_edits_created_at", "created_at"),
    )


class MessageVersion(Base):
    """Model for message version history."""
    __tablename__ = "message_versions"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"))
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Version data
    version_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    version_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="versions")
    creator = relationship("UserModel")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_message_versions_message_id", "message_id"),
        Index("idx_message_versions_version", "message_id", "version_number"),
        Index("idx_message_versions_created_at", "created_at"),
    )


class AIProcessingStep(Base):
    """Model for AI processing steps."""
    __tablename__ = "ai_processing_steps"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"))
    
    # Processing data
    stage: Mapped[str] = mapped_column(String(50))
    step_name: Mapped[str] = mapped_column(String(100))
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="processing_steps")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_ai_processing_steps_message_id", "message_id"),
        Index("idx_ai_processing_steps_stage", "stage"),
        Index("idx_ai_processing_steps_status", "message_id", "stage", "completed_at"),
        Index("idx_ai_processing_steps_timing", "started_at", "completed_at"),
    )


class MessageSearchIndex(Base):
    """Model for message search indexing."""
    __tablename__ = "message_search_indexes"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys (unique constraint for one index per message)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), unique=True)
    
    # Search data
    content_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Serialized embedding vector
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    topics: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    entities: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)  # {"person": ["John", "Jane"], "location": ["NYC"]}
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Timestamps
    indexed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="search_index", uselist=False)
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_message_search_message_id", "message_id"),
        Index("idx_message_search_keywords", "keywords", postgresql_using="gin"),
        Index("idx_message_search_topics", "topics", postgresql_using="gin"),
        Index("idx_message_search_sentiment", "sentiment_score"),
        Index("idx_message_search_language", "language"),
        Index("idx_message_search_indexed_at", "indexed_at"),
    )