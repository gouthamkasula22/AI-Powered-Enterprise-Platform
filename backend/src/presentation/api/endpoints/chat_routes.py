"""
Chat API Endpoints

This module contains the FastAPI endpoints for the chat API.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import json

# Import dependencies
from ..dependencies.auth import get_current_user
from ..dependencies.chat_dependencies import get_chat_service
from ....domain.entities.user import User
from ....application.services import EnhancedChatService

# Import schemas from new location
from ..schemas.chat import (
    ThreadCreate, ThreadUpdate, ThreadResponse, ThreadsResponse,
    MessageCreate, MessageResponse, StreamResponse
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    data: ThreadCreate,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Create a new chat thread."""
    # Ensure user id is not None before proceeding
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required to create a thread"
        )
        
    thread = await chat_service.create_thread(
        user_id=current_user.id,
        title=data.title,
        meta_data=data.metadata
    )
    
    # Ensure the thread has an ID after creation
    assert thread.id is not None, "Thread should have an ID after creation"
    
    return ThreadResponse(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at or datetime.utcnow(),
        updated_at=thread.updated_at or datetime.utcnow(),
        metadata=thread.meta_data,
        user_id=thread.user_id
    )


@router.get("/threads", response_model=ThreadsResponse)
async def get_threads(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Get all chat threads for the current user."""
    # Ensure user id is not None before proceeding
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required to get threads"
        )
        
    threads = await chat_service.get_user_threads(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    count = await chat_service.thread_repository.count_by_user_id(current_user.id)
    
    return ThreadsResponse(
        threads=[
            ThreadResponse(
                id=thread.id if thread.id is not None else 0,  # This should never be None for existing threads
                title=thread.title,
                created_at=thread.created_at or datetime.utcnow(),
                updated_at=thread.updated_at or datetime.utcnow(),
                metadata=thread.meta_data,
                user_id=thread.user_id
            )
            for thread in threads
        ],
        total=count
    )


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Get a chat thread by ID."""
    thread = await chat_service.get_thread(thread_id)
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this thread"
        )
    
    messages = await chat_service.get_thread_messages(thread_id)
    
    # Ensure thread has an ID (it should for existing threads)
    assert thread.id is not None, "Thread should have an ID"
    
    return ThreadResponse(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at or datetime.utcnow(),
        updated_at=thread.updated_at or datetime.utcnow(),
        metadata=thread.meta_data,
        user_id=thread.user_id,
        messages=[
            MessageResponse(
                id=message.id if message.id is not None else 0,  # Should never be None for existing messages
                thread_id=message.thread_id,
                content=message.content,
                role=message.role.value,
                status=message.status.value,
                created_at=message.created_at or datetime.utcnow(),
                updated_at=message.updated_at or datetime.utcnow(),
                metadata=message.meta_data,
                user_id=message.user_id
            )
            for message in messages
        ]
    )


@router.put("/threads/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: int,
    data: ThreadUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Update a chat thread."""
    thread = await chat_service.get_thread(thread_id)
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this thread"
        )
    
    updated_thread = await chat_service.update_thread(
        thread_id=thread_id,
        title=data.title,
        meta_data=data.metadata
    )
    
    if not updated_thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found after update"
        )
    
    return ThreadResponse(
        id=updated_thread.id or 0,  # Should never be None for existing thread
        title=updated_thread.title,
        created_at=updated_thread.created_at or datetime.utcnow(),
        updated_at=updated_thread.updated_at or datetime.utcnow(),
        metadata=updated_thread.meta_data,
        user_id=updated_thread.user_id
    )


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Delete a chat thread."""
    thread = await chat_service.get_thread(thread_id)
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this thread"
        )
    
    success = await chat_service.delete_thread(thread_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete thread"
        )


@router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def create_message(
    thread_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Create a new message in a thread."""
    thread = await chat_service.get_thread(thread_id)
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this thread"
        )
    
    # Ensure user id is not None before proceeding
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required to create a message"
        )
    
    message = await chat_service.create_user_message(
        thread_id=thread_id,
        user_id=current_user.id,
        content=data.content,
        meta_data=data.metadata
    )
    
    # Ensure message has an ID after creation
    assert message.id is not None, "Message should have an ID after creation"
    
    return MessageResponse(
        id=message.id,
        thread_id=message.thread_id,
        content=message.content,
        role=message.role.value,
        status=message.status.value,
        created_at=message.created_at or datetime.utcnow(),
        updated_at=message.updated_at or datetime.utcnow(),
        metadata=message.meta_data,
        user_id=message.user_id
    )


@router.get("/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Get all messages in a thread."""
    thread = await chat_service.get_thread(thread_id)
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this thread"
        )
    
    messages = await chat_service.get_thread_messages(thread_id)
    
    return [
        MessageResponse(
            id=message.id if message.id is not None else 0,  # Should never be None for existing messages
            thread_id=message.thread_id,
            content=message.content,
            role=message.role.value,
            status=message.status.value,
            created_at=message.created_at or datetime.utcnow(),
            updated_at=message.updated_at or datetime.utcnow(),
            metadata=message.meta_data,
            user_id=message.user_id
        )
        for message in messages
    ]


@router.post("/threads/{thread_id}/messages/stream")
async def stream_assistant_response(
    thread_id: int,
    data: MessageCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Stream a response from the assistant."""
    thread = await chat_service.get_thread(thread_id)
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this thread"
        )
    
    # Ensure user id is not None before proceeding
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required to create a message"
        )
    
    # First, save the user's message
    await chat_service.create_user_message(
        thread_id=thread_id,
        user_id=current_user.id,
        content=data.content,
        meta_data=data.metadata
    )
    
    # Server-sent events streaming response
    async def event_generator():
        try:
            # Stream the assistant's response
            if current_user.id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User ID is required to stream responses"
                )
                
            async for chunk in chat_service.stream_assistant_response(
                thread_id=thread_id,
                user_id=current_user.id
            ):
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                # Format as SSE
                yield f"data: {json.dumps(chunk)}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.05)
        except Exception as e:
            # Handle errors
            error_message = f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            yield error_message
        finally:
            # End the stream
            yield "data: {\"done\": true}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# AI-Powered Endpoints
class AIMessageRequest(BaseModel):
    """Request schema for AI message generation"""
    message: str = Field(..., description="User message to get AI response for")
    model: Optional[str] = Field(None, description="AI model to use (e.g., gpt-4o, gpt-4o-mini)")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Response creativity (0.0-2.0)")
    max_tokens: Optional[int] = Field(None, ge=1, le=4096, description="Maximum response tokens")


@router.post("/threads/{thread_id}/ai-response", response_model=MessageResponse)
async def generate_ai_response(
    thread_id: int,
    data: AIMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Generate an AI response to a user message in a thread."""
    # Validate thread access
    thread = await chat_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this thread"
        )
    
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required"
        )
    
    try:
        # Parse model if provided
        model = None
        if data.model:
            from ....infrastructure.ai.config import AIModel
            try:
                model = AIModel(data.model)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid model: {data.model}"
                )
        
        # Generate AI response
        assert current_user.id is not None  # Already validated above
        ai_message = await chat_service.generate_ai_response(
            thread_id=thread_id,
            user_id=current_user.id,
            user_message=data.message,
            model=model,
            temperature=data.temperature,
            max_tokens=data.max_tokens
        )
        
        return MessageResponse(
            id=ai_message.id or 0,
            thread_id=ai_message.thread_id,
            user_id=ai_message.user_id,
            content=ai_message.content,
            role=ai_message.role.value,
            status=ai_message.status.value,
            created_at=ai_message.created_at or datetime.utcnow(),
            updated_at=ai_message.updated_at,
            metadata=ai_message.meta_data or {}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI response: {str(e)}"
        )


@router.post("/threads/{thread_id}/ai-stream")
async def stream_ai_response(
    thread_id: int,
    data: AIMessageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service)
):
    """Stream an AI response to a user message in a thread."""
    # Validate thread access
    thread = await chat_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this thread"
        )
    
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required"
        )
    
    # Parse model if provided
    model = None
    if data.model:
        from ....infrastructure.ai.config import AIModel
        try:
            model = AIModel(data.model)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model: {data.model}"
            )
    
    # Server-sent events streaming response
    async def event_generator():
        try:
            assert current_user.id is not None  # Already validated above
            async for chunk in chat_service.generate_ai_streaming_response(
                thread_id=thread_id,
                user_id=current_user.id,
                user_message=data.message,
                model=model,
                temperature=data.temperature,
                max_tokens=data.max_tokens
            ):
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                # Format as SSE
                yield f"data: {json.dumps(chunk)}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.02)
                
                if chunk.get("is_complete", False):
                    break
                    
        except Exception as e:
            # Handle errors
            error_data = {
                "error": str(e),
                "is_complete": True,
                "message_id": None
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        finally:
            # End the stream
            yield "data: {\"done\": true}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/ai/status")
async def get_ai_status(
    current_user: User = Depends(get_current_user)
):
    """Get AI service status and available models."""
    from ....application.services.ai_service import ai_service
    
    return ai_service.get_service_status()


@router.post("/threads/{thread_id}/summary")
async def get_conversation_summary(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: EnhancedChatService = Depends(get_chat_service),
    max_length: int = 200
):
    """Generate an AI summary of the conversation."""
    # Validate thread access
    thread = await chat_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this thread"
        )
    
    try:
        summary = await chat_service.get_ai_conversation_summary(
            thread_id=thread_id,
            max_length=max_length
        )
        
        return {"summary": summary}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )
