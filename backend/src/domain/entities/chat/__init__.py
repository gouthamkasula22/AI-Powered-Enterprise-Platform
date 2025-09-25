"""
Chat Domain Entities Module

This module exports all chat-related domain entities with enhanced features
for advanced thread management, message processing, and document handling.
"""

from .chat_entities import (
    # Enums
    ThreadStatus,
    ThreadCategory,
    MessageRole,
    MessageStatus,
    MessageType,
    DocumentType,
    ProcessingStatus,
    
    # Entities
    ChatThread,
    ChatMessage,
    Document,
    DocumentChunk
)

__all__ = [
    # Enums
    "ThreadStatus",
    "ThreadCategory",
    "MessageRole",
    "MessageStatus",
    "MessageType",
    "DocumentType",
    "ProcessingStatus",
    
    # Entities
    "ChatThread",
    "ChatMessage",
    "Document",
    "DocumentChunk"
]