"""
Enhanced Message Processing Repository Interfaces

This module defines repository interfaces for advanced message processing features
including reactions, editing, version history, and AI processing pipeline.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from ..entities.message_processing import (
    MessageReaction, MessageEdit, MessageVersion, 
    AIProcessingStep, MessageSearchIndex, MessageProcessingPipeline,
    ReactionType, EditType, ProcessingStage
)


class MessageReactionRepository(ABC):
    """Repository interface for message reactions."""
    
    @abstractmethod
    async def create(self, reaction: MessageReaction) -> MessageReaction:
        """Create a new message reaction."""
        pass
    
    @abstractmethod
    async def get_by_id(self, reaction_id: int) -> Optional[MessageReaction]:
        """Get a reaction by ID."""
        pass
    
    @abstractmethod
    async def delete(self, reaction_id: int) -> bool:
        """Delete a reaction."""
        pass
    
    @abstractmethod
    async def get_by_message(self, message_id: int) -> List[MessageReaction]:
        """Get all reactions for a message."""
        pass
    
    @abstractmethod
    async def get_by_user_message(self, user_id: int, message_id: int) -> List[MessageReaction]:
        """Get reactions by a user for a specific message."""
        pass
    
    @abstractmethod
    async def get_reaction_counts(self, message_id: int) -> Dict[ReactionType, int]:
        """Get reaction counts by type for a message."""
        pass
    
    @abstractmethod
    async def toggle_reaction(
        self, 
        user_id: int, 
        message_id: int, 
        reaction_type: ReactionType,
        custom_emoji: Optional[str] = None
    ) -> Tuple[bool, Optional[MessageReaction]]:
        """Toggle a reaction (add if not exists, remove if exists). Returns (is_added, reaction)."""
        pass
    
    @abstractmethod
    async def get_user_reactions(self, user_id: int, limit: int = 50) -> List[MessageReaction]:
        """Get recent reactions by a user."""
        pass


class MessageEditRepository(ABC):
    """Repository interface for message edit history."""
    
    @abstractmethod
    async def create(self, edit: MessageEdit) -> MessageEdit:
        """Create a new message edit record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, edit_id: int) -> Optional[MessageEdit]:
        """Get an edit by ID."""
        pass
    
    @abstractmethod
    async def get_by_message(self, message_id: int) -> List[MessageEdit]:
        """Get all edits for a message, ordered by creation time."""
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: int, limit: int = 50) -> List[MessageEdit]:
        """Get recent edits by a user."""
        pass
    
    @abstractmethod
    async def get_edit_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get edit statistics for a user."""
        pass


class MessageVersionRepository(ABC):
    """Repository interface for message version history."""
    
    @abstractmethod
    async def create(self, version: MessageVersion) -> MessageVersion:
        """Create a new message version."""
        pass
    
    @abstractmethod
    async def get_by_id(self, version_id: int) -> Optional[MessageVersion]:
        """Get a version by ID."""
        pass
    
    @abstractmethod
    async def get_by_message(self, message_id: int) -> List[MessageVersion]:
        """Get all versions for a message, ordered by version number."""
        pass
    
    @abstractmethod
    async def get_current_version(self, message_id: int) -> Optional[MessageVersion]:
        """Get the current version of a message."""
        pass
    
    @abstractmethod
    async def get_version_by_number(self, message_id: int, version_number: int) -> Optional[MessageVersion]:
        """Get a specific version of a message."""
        pass
    
    @abstractmethod
    async def create_new_version(
        self, 
        message_id: int, 
        content: str,
        created_by: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageVersion:
        """Create a new version for a message."""
        pass


class AIProcessingStepRepository(ABC):
    """Repository interface for AI processing steps."""
    
    @abstractmethod
    async def create(self, step: AIProcessingStep) -> AIProcessingStep:
        """Create a new processing step."""
        pass
    
    @abstractmethod
    async def update(self, step: AIProcessingStep) -> AIProcessingStep:
        """Update a processing step."""
        pass
    
    @abstractmethod
    async def get_by_id(self, step_id: int) -> Optional[AIProcessingStep]:
        """Get a processing step by ID."""
        pass
    
    @abstractmethod
    async def get_by_message(self, message_id: int) -> List[AIProcessingStep]:
        """Get all processing steps for a message."""
        pass
    
    @abstractmethod
    async def get_by_stage(self, message_id: int, stage: ProcessingStage) -> List[AIProcessingStep]:
        """Get processing steps for a specific stage."""
        pass
    
    @abstractmethod
    async def get_active_processing(self) -> List[AIProcessingStep]:
        """Get currently active processing steps."""
        pass
    
    @abstractmethod
    async def get_failed_processing(self, limit: int = 50) -> List[AIProcessingStep]:
        """Get failed processing steps."""
        pass
    
    @abstractmethod
    async def mark_completed(
        self, 
        step_id: int, 
        output_data: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None
    ) -> bool:
        """Mark a processing step as completed."""
        pass
    
    @abstractmethod
    async def mark_failed(self, step_id: int, error_message: str) -> bool:
        """Mark a processing step as failed."""
        pass
    
    @abstractmethod
    async def get_processing_analytics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get processing analytics and performance metrics."""
        pass


class MessageSearchIndexRepository(ABC):
    """Repository interface for message search indexing."""
    
    @abstractmethod
    async def create(self, index: MessageSearchIndex) -> MessageSearchIndex:
        """Create a new search index."""
        pass
    
    @abstractmethod
    async def update(self, index: MessageSearchIndex) -> MessageSearchIndex:
        """Update a search index."""
        pass
    
    @abstractmethod
    async def get_by_message_id(self, message_id: int) -> Optional[MessageSearchIndex]:
        """Get search index for a message."""
        pass
    
    @abstractmethod
    async def search_by_keywords(
        self, 
        keywords: List[str], 
        thread_ids: Optional[List[int]] = None,
        limit: int = 50
    ) -> List[MessageSearchIndex]:
        """Search messages by keywords."""
        pass
    
    @abstractmethod
    async def search_by_topics(
        self, 
        topics: List[str],
        thread_ids: Optional[List[int]] = None,
        limit: int = 50
    ) -> List[MessageSearchIndex]:
        """Search messages by topics."""
        pass
    
    @abstractmethod
    async def search_by_entities(
        self, 
        entity_type: str, 
        entity_values: List[str],
        thread_ids: Optional[List[int]] = None,
        limit: int = 50
    ) -> List[MessageSearchIndex]:
        """Search messages by entities."""
        pass
    
    @abstractmethod
    async def search_by_sentiment(
        self, 
        min_score: float, 
        max_score: float,
        thread_ids: Optional[List[int]] = None,
        limit: int = 50
    ) -> List[MessageSearchIndex]:
        """Search messages by sentiment score range."""
        pass
    
    @abstractmethod
    async def semantic_search(
        self, 
        query_vector: str, 
        thread_ids: Optional[List[int]] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Tuple[MessageSearchIndex, float]]:
        """Perform semantic search using vector similarity."""
        pass
    
    @abstractmethod
    async def get_unindexed_messages(self, limit: int = 100) -> List[int]:
        """Get message IDs that need indexing."""
        pass
    
    @abstractmethod
    async def bulk_update_indexes(self, indexes: List[MessageSearchIndex]) -> int:
        """Bulk update search indexes. Returns count of updated records."""
        pass


class MessageProcessingPipelineRepository(ABC):
    """Repository interface for complete message processing pipeline."""
    
    @abstractmethod
    async def get_pipeline(self, message_id: int) -> MessageProcessingPipeline:
        """Get the complete processing pipeline for a message."""
        pass
    
    @abstractmethod
    async def create_pipeline(self, message_id: int) -> MessageProcessingPipeline:
        """Initialize a new processing pipeline for a message."""
        pass
    
    @abstractmethod
    async def get_processing_queue(self, limit: int = 50) -> List[int]:
        """Get message IDs in the processing queue."""
        pass
    
    @abstractmethod
    async def get_failed_pipelines(self, limit: int = 50) -> List[MessageProcessingPipeline]:
        """Get pipelines with failed processing."""
        pass
    
    @abstractmethod
    async def get_pipeline_analytics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics for processing pipelines."""
        pass
    
    @abstractmethod
    async def retry_failed_processing(self, message_id: int) -> bool:
        """Retry failed processing for a message."""
        pass