"""
Database Models Module

Contains SQLAlchemy models for the database layer.
"""

# Import Base first
from ..config import Base

from .user_model import (
    UserModel,
    OAuthAccountModel,
    SessionModel,
    AuditLogModel
)

from .chat_models import (
    ChatThread,
    ChatMessage,
    Document,
    DocumentChunk
)

from .message_processing_models import (
    MessageReaction,
    MessageEdit, 
    MessageVersion,
    AIProcessingStep,
    MessageSearchIndex
)

from .chat_auth_models import (
    ChatUserRole,
    ThreadAccess,
    ChatAuditLog,
    UserChatIsolation,
    ChatRateLimit
)

from .image_models import (
    GeneratedImage,
    ImageGenerationTask,
    ImageGalleryCollection
)

__all__ = [
    "Base",  # Add Base to exports
    "UserModel", 
    "OAuthAccountModel",
    "SessionModel",
    "AuditLogModel",
    "ChatThread",
    "ChatMessage",
    "Document",
    "MessageReaction",
    "MessageEdit",
    "MessageVersion", 
    "AIProcessingStep",
    "MessageSearchIndex",
    "ChatUserRole",
    "ThreadAccess", 
    "ChatAuditLog",
    "UserChatIsolation",
    "ChatRateLimit",
    "GeneratedImage",
    "ImageGenerationTask",
    "ImageGalleryCollection"
]