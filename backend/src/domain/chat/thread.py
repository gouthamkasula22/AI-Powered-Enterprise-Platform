"""
Chat Thread Entity

This module defines the ChatThread entity for the chat domain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class ChatThread:
    """
    Chat Thread Entity
    
    Represents a conversation thread in the chat system.
    """
    title: str
    user_id: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None
