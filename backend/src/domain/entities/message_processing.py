"""
Enhanced Message Processing Entities

This module defines enhanced entities for advanced message processing,
including reactions, editing, version history, and AI processing.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
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


@dataclass(frozen=True)
class MessageReaction:
    """Represents a user reaction to a message."""
    id: int
    message_id: int
    user_id: int
    reaction_type: ReactionType
    custom_emoji: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_custom(self) -> bool:
        """Check if this is a custom reaction."""
        return self.reaction_type == ReactionType.CUSTOM and self.custom_emoji is not None
    
    def display_text(self) -> str:
        """Get display text for the reaction."""
        if self.is_custom():
            return self.custom_emoji or ""
        
        emoji_map = {
            ReactionType.THUMBS_UP: "👍",
            ReactionType.THUMBS_DOWN: "👎", 
            ReactionType.HEART: "❤️",
            ReactionType.LAUGH: "😂",
            ReactionType.SURPRISED: "😮",
            ReactionType.ANGRY: "😠",
            ReactionType.CONFUSED: "😕"
        }
        return emoji_map.get(self.reaction_type, "")


@dataclass(frozen=True)
class MessageEdit:
    """Represents an edit to a message."""
    id: int
    message_id: int
    user_id: int
    edit_type: EditType
    old_content: str
    new_content: str
    reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def content_changed(self) -> bool:
        """Check if the actual content was changed."""
        return self.old_content != self.new_content
    
    def get_diff_summary(self) -> Dict[str, Any]:
        """Get a summary of changes made."""
        old_length = len(self.old_content)
        new_length = len(self.new_content)
        
        return {
            "characters_added": max(0, new_length - old_length),
            "characters_removed": max(0, old_length - new_length),
            "edit_type": self.edit_type.value,
            "has_reason": self.reason is not None
        }


@dataclass(frozen=True)
class MessageVersion:
    """Represents a version in message history."""
    id: int
    message_id: int
    version_number: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_current_version(self, current_version: int) -> bool:
        """Check if this is the current version."""
        return self.version_number == current_version
    
    def get_content_preview(self, max_length: int = 100) -> str:
        """Get a preview of the content."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length - 3] + "..."


@dataclass(frozen=True)
class AIProcessingStep:
    """Represents a step in AI message processing."""
    id: int
    message_id: int
    stage: ProcessingStage
    step_name: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def is_completed(self) -> bool:
        """Check if this step is completed."""
        return self.completed_at is not None
    
    def is_successful(self) -> bool:
        """Check if this step completed successfully."""
        return self.is_completed() and self.error_message is None
    
    def get_duration(self) -> Optional[int]:
        """Get processing duration in milliseconds."""
        if self.processing_time_ms:
            return self.processing_time_ms
        
        if self.is_completed() and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        
        return None


@dataclass(frozen=True)
class MessageSearchIndex:
    """Represents search index data for a message."""
    id: int
    message_id: int
    content_vector: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    sentiment_score: Optional[float] = None
    language: Optional[str] = None
    indexed_at: datetime = field(default_factory=datetime.utcnow)
    
    def has_keyword(self, keyword: str) -> bool:
        """Check if message contains a specific keyword."""
        return keyword.lower() in [k.lower() for k in self.keywords]
    
    def has_topic(self, topic: str) -> bool:
        """Check if message is related to a specific topic."""
        return topic.lower() in [t.lower() for t in self.topics]
    
    def get_entities_by_type(self, entity_type: str) -> List[str]:
        """Get entities of a specific type."""
        return self.entities.get(entity_type, [])
    
    def is_positive_sentiment(self) -> bool:
        """Check if message has positive sentiment."""
        return self.sentiment_score is not None and self.sentiment_score > 0.1
    
    def is_negative_sentiment(self) -> bool:
        """Check if message has negative sentiment."""
        return self.sentiment_score is not None and self.sentiment_score < -0.1


@dataclass(frozen=True)
class MessageProcessingPipeline:
    """Represents the complete processing pipeline for a message."""
    message_id: int
    steps: List[AIProcessingStep] = field(default_factory=list)
    search_index: Optional[MessageSearchIndex] = None
    reactions: List[MessageReaction] = field(default_factory=list)
    edits: List[MessageEdit] = field(default_factory=list)
    versions: List[MessageVersion] = field(default_factory=list)
    
    def get_current_stage(self) -> ProcessingStage:
        """Get the current processing stage."""
        if not self.steps:
            return ProcessingStage.RECEIVED
        
        # Get the latest step
        latest_step = max(self.steps, key=lambda s: s.started_at)
        return latest_step.stage
    
    def is_processing_complete(self) -> bool:
        """Check if processing is complete."""
        current_stage = self.get_current_stage()
        return current_stage in [ProcessingStage.COMPLETED, ProcessingStage.FAILED]
    
    def get_failed_steps(self) -> List[AIProcessingStep]:
        """Get steps that failed."""
        return [step for step in self.steps if step.error_message is not None]
    
    def get_total_processing_time(self) -> int:
        """Get total processing time in milliseconds."""
        completed_steps = [step for step in self.steps if step.is_completed()]
        return sum(step.get_duration() or 0 for step in completed_steps)
    
    def get_reaction_counts(self) -> Dict[ReactionType, int]:
        """Get count of reactions by type."""
        counts = {}
        for reaction in self.reactions:
            counts[reaction.reaction_type] = counts.get(reaction.reaction_type, 0) + 1
        return counts
    
    def get_edit_history(self) -> List[MessageEdit]:
        """Get edit history sorted by creation time."""
        return sorted(self.edits, key=lambda e: e.created_at)
    
    def get_current_version(self) -> Optional[MessageVersion]:
        """Get the current version of the message."""
        if not self.versions:
            return None
        
        return max(self.versions, key=lambda v: v.version_number)
    
    def has_been_edited(self) -> bool:
        """Check if the message has been edited."""
        return len(self.edits) > 0