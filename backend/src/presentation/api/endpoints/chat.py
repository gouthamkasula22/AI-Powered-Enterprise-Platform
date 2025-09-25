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
from ..dependencies.chat import get_chat_service
from ....domain.entities.user import User
from ....application.services.chat_service import ChatService

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
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a new chat thread."""
    thread = await chat_service.create_thread(
        user_id=current_user.id,
        title=data.title,
        metadata=data.metadata
    )
    
    return ThreadResponse(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        metadata=thread.metadata
    )


@router.get("/threads", response_model=ThreadsResponse)
async def get_threads(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get all chat threads for the current user."""
    threads = await chat_service.get_user_threads(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    count = await chat_service.thread_repository.count_by_user_id(current_user.id)
    
    return ThreadsResponse(
        threads=[
            ThreadResponse(
                id=thread.id,
                title=thread.title,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                metadata=thread.metadata
            )
            for thread in threads
        ],
        total=count
    )


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
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
    
    return ThreadResponse(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        metadata=thread.metadata,
        messages=[
            MessageResponse(
                id=message.id,
                thread_id=message.thread_id,
                content=message.content,
                role=message.role.value,
                status=message.status.value,
                created_at=message.created_at,
                updated_at=message.updated_at,
                metadata=message.metadata
            )
            for message in messages
        ]
    )


@router.put("/threads/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: int,
    data: ThreadUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
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
    
    thread.title = data.title
    thread.metadata = data.metadata
    
    updated_thread = await chat_service.update_thread(thread)
    
    return ThreadResponse(
        id=updated_thread.id,
        title=updated_thread.title,
        created_at=updated_thread.created_at,
        updated_at=updated_thread.updated_at,
        metadata=updated_thread.metadata
    )


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
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
    chat_service: ChatService = Depends(get_chat_service)
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
    
    message = await chat_service.create_user_message(
        thread_id=thread_id,
        user_id=current_user.id,
        content=data.content,
        metadata=data.metadata
    )
    
    return MessageResponse(
        id=message.id,
        thread_id=message.thread_id,
        content=message.content,
        role=message.role.value,
        status=message.status.value,
        created_at=message.created_at,
        updated_at=message.updated_at,
        metadata=message.metadata
    )


@router.get("/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
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
            id=message.id,
            thread_id=message.thread_id,
            content=message.content,
            role=message.role.value,
            status=message.status.value,
            created_at=message.created_at,
            updated_at=message.updated_at,
            metadata=message.metadata
        )
        for message in messages
    ]


@router.post("/threads/{thread_id}/messages/stream")
async def stream_assistant_response(
    thread_id: int,
    data: MessageCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
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
    
    # First, save the user's message
    await chat_service.create_user_message(
        thread_id=thread_id,
        user_id=current_user.id,
        content=data.content,
        metadata=data.metadata
    )
    
    # Server-sent events streaming response
    async def event_generator():
        try:
            # Stream the assistant's response
            async for chunk in chat_service.stream_assistant_response(
                thread_id=thread_id,
                user_id=current_user.id,
                prompt=data.content
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
        )


@router.get("/threads/{thread_id}", response_model=ThreadWithMessages)
async def get_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get a specific thread with its messages"""
    try:
        thread = await chat_service.get_thread(thread_id=thread_id, user_id=current_user.id)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread with ID {thread_id} not found"
            )
        
        # Get messages for this thread
        messages = await chat_service.get_messages_by_thread(thread_id=thread_id)
        
        # Combine thread with messages
        thread_dict = {}
        for attr, value in vars(thread).items():
            if not attr.startswith('_'):
                thread_dict[attr] = value
                
        thread_with_messages = ThreadWithMessages(
            **thread_dict,
            messages=[MessageResponse.model_validate(msg) for msg in messages]
        )
        
        return thread_with_messages
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve thread: {str(e)}"
        )


@router.put("/threads/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: int,
    thread_data: ThreadUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Update a chat thread"""
    try:
        # Get the thread first to check ownership
        thread = await chat_service.get_thread(thread_id=thread_id, user_id=current_user.id)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread with ID {thread_id} not found"
            )
            
        # Update fields that are provided
        update_data = {}
        if thread_data.title is not None:
            update_data["title"] = thread_data.title
        if thread_data.metadata is not None:
            update_data["metadata"] = thread_data.metadata
            
        if not update_data:
            return thread  # Nothing to update
            
        updated_thread = await chat_service.update_thread(
            thread_id=thread_id,
            user_id=current_user.id,
            **update_data
        )
        
        return updated_thread
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update thread: {str(e)}"
        )


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Delete a chat thread"""
    try:
        # Get the thread first to check ownership
        thread = await chat_service.get_thread(thread_id=thread_id, user_id=current_user.id)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread with ID {thread_id} not found"
            )
            
        await chat_service.delete_thread(thread_id=thread_id, user_id=current_user.id)
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete thread: {str(e)}"
        )


@router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def create_message(
    thread_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Add a new message to a thread"""
    try:
        # Check if thread exists and belongs to user
        thread = await chat_service.get_thread(thread_id=thread_id, user_id=current_user.id)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread with ID {thread_id} not found"
            )
            
        message = await chat_service.add_message(
            thread_id=thread_id,
            user_id=current_user.id,
            content=message_data.content,
            role=message_data.role,
            metadata=message_data.metadata
        )
        
        return message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}"
        )


@router.get("/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get all messages for a thread"""
    try:
        # Check if thread exists and belongs to user
        thread = await chat_service.get_thread(thread_id=thread_id, user_id=current_user.id)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread with ID {thread_id} not found"
            )
            
        messages = await chat_service.get_messages_by_thread(thread_id=thread_id)
        return messages
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        )


@router.post("/threads/{thread_id}/assistant")
async def get_assistant_response(
    thread_id: int,
    request: Optional[ChatAssistantRequest] = None,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get a non-streaming response from the assistant for a thread"""
    try:
        # Check if thread exists and belongs to user
        thread = await chat_service.get_thread(thread_id=thread_id, user_id=current_user.id)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread with ID {thread_id} not found"
            )
        
        # Set default values if request is None
        model = None
        temperature = 0.7
        
        if request:
            model = request.model
            temperature = request.temperature
            
        # Get response from assistant
        message = await chat_service.get_assistant_response(
            thread_id=thread_id,
            user_id=current_user.id,
            model=model,
            temperature=temperature
        )
        
        # Convert domain entity to response model
        message_dict = {}
        for attr, value in vars(message).items():
            if not attr.startswith('_'):
                message_dict[attr] = value
                
        return MessageResponse.model_validate(message_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assistant response: {str(e)}"
        )


@router.post("/threads/{thread_id}/stream")
async def stream_assistant_response(
    thread_id: int,
    request: Optional[ChatAssistantRequest] = None,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Stream an assistant response for a thread"""
    
    async def event_generator():
        try:
            # Set default values if request is None
            model = None
            temperature = 0.7
            
            if request:
                model = request.model
                temperature = request.temperature
                
            # Stream response
            async for content, is_complete in chat_service.stream_assistant_response(
                thread_id=thread_id,
                user_id=current_user.id,
                model=model,
                temperature=temperature
            ):
                # Format as Server-Sent Event
                yield f"data: {content}\n"
                
                if is_complete:
                    yield f"event: complete\ndata: true\n\n"
                    break
                    
                yield "\n"  # End of event
                
        except ValueError as e:
            # Handle permission errors
            error_message = str(e)
            yield f"event: error\ndata: {error_message}\n\n"
            
        except Exception as e:
            # Handle other errors
            error_message = f"Error: {str(e)}"
            yield f"event: error\ndata: {error_message}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )