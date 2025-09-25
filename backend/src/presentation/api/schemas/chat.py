"""
Chat API Schemas

This module contains the Pydantic models for the chat API.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union, Literal


class ThreadCreate(BaseModel):
    """Request schema for creating a new chat thread"""
    title: str = Field(..., min_length=1, max_length=255)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ThreadUpdate(BaseModel):
    """Request schema for updating a chat thread"""
    title: str = Field(..., min_length=1, max_length=255)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ThreadResponse(BaseModel):
    """Response schema for a chat thread"""
    id: int
    title: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    messages: Optional[List['MessageResponse']] = None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Request schema for creating a new chat message"""
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    """Response schema for a chat message"""
    id: int
    thread_id: int
    user_id: int
    content: str
    role: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ThreadsResponse(BaseModel):
    """Response schema for a list of chat threads"""
    threads: List[ThreadResponse]
    total: int


class StreamResponse(BaseModel):
    """Response schema for a chat stream chunk"""
    id: int
    content: str
    is_complete: bool


class ChatAssistantRequest(BaseModel):
    """Request schema for getting an assistant response"""
    model: Optional[str] = Field(None)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "default",
                "temperature": 0.7
            }
        }
