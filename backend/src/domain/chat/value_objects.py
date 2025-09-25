"""
Chat Value Objects

This module contains value objects for the chat domain,
such as message roles, statuses, and document types.
"""

from enum import Enum


class MessageRole(str, Enum):
    """
    Role of a message in a chat conversation
    
    USER: Message from the user
    ASSISTANT: Message from the AI assistant
    SYSTEM: System message (instructions, notifications)
    """
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"
    
    def __str__(self) -> str:
        return self.value


class MessageStatus(str, Enum):
    """
    Status of a message in a chat conversation
    
    PENDING: Message is waiting to be processed
    DELIVERED: Message has been successfully processed and delivered
    FAILED: Message processing failed
    """
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    
    def __str__(self) -> str:
        return self.value


class DocumentType(str, Enum):
    """
    Type of a document in the chat system
    
    PDF: PDF document
    TXT: Plain text document
    CSV: CSV spreadsheet
    IMAGE: Image file
    OTHER: Other document type
    """
    PDF = "PDF"
    TXT = "TXT"
    CSV = "CSV"
    IMAGE = "IMAGE"
    OTHER = "OTHER"
    
    def __str__(self) -> str:
        return self.value
