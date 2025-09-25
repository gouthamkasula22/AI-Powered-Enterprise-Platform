"""
Chat Message Entity

This module defines the ChatMessage entity for the chat domain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from .value_objects import MessageRole, MessageStatus


@dataclass
class ChatMessage:
    """
    Chat Message Entity
    
    Represents a message in a chat thread.
    """
    thread_id: int
    content: str
    role: MessageRole
    user_id: int
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None
