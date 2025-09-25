"""
Document Entity

This module defines the Document entity for the chat domain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from .value_objects import DocumentType


@dataclass
class Document:
    """
    Document Entity
    
    Represents a document uploaded to a chat thread.
    """
    thread_id: int
    user_id: int
    filename: str
    mime_type: str
    content_hash: str
    size_bytes: int
    document_type: DocumentType
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    content: Optional[str] = None
    id: Optional[int] = None
