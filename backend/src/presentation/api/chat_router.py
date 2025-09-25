"""
Chat API Router

FastAPI router for chat endpoints including REST API and WebSocket support.
Integrates with the RAG system for intelligent responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ...shared.exceptions import (
    ValidationError, 
    NotFoundError, 
    ProcessingError,
    AIError
)
from ...infrastructure.database.database import get_db_session
from ...infrastructure.ai.conversation_manager import ConversationManager
from ...infrastructure.ai.query_processor import QueryProcessor
from ...infrastructure.ai.context_manager import ContextManager
from ...infrastructure.ai.prompt_manager import PromptManager
from ...infrastructure.ai.llm_service import LLMService
from ...infrastructure.database.models import ChatThread, ChatMessage, UserModel


# Pydantic Models for API
class CreateConversationRequest(BaseModel):
    """Request model for creating a new conversation."""
    title: str = Field(..., min_length=1, max_length=255, description="Conversation title")
    category: Optional[str] = Field("general", description="Conversation category")
    tags: Optional[List[str]] = Field(None, description="Optional tags for the conversation")


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    content: str = Field(..., min_length=1, description="Message content")
    message_type: Optional[str] = Field("text", description="Type of message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the message")


class ConversationResponse(BaseModel):
    """Response model for conversation data."""
    id: int
    title: str
    user_id: int
    status: str
    category: str
    tags: Optional[List[str]]
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_at: Optional[datetime]


class MessageResponse(BaseModel):
    """Response model for message data."""
    id: int
    conversation_id: int
    user_id: Optional[int]
    content: str
    message_type: str
    role: str
    created_at: datetime
    is_ai_response: bool
    processing_time_ms: Optional[int]
    model_used: Optional[str]


class ConversationListResponse(BaseModel):
    """Response model for conversation list."""
    conversations: List[ConversationResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ChatStreamMessage(BaseModel):
    """Model for streaming chat messages."""
    type: str  # "message_chunk", "message_complete", "error", "status"
    content: Optional[str] = None
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


# Router and dependency setup
router = APIRouter(tags=["chat"])


async def get_current_user_id() -> int:
    """Get current user ID from authentication context."""
    # TODO: Implement proper JWT authentication
    # For now, return a default user ID for testing
    return 1


async def get_chat_services(
    session: AsyncSession = Depends(get_db_session)
) -> tuple:
    """Get chat service dependencies."""
    conversation_manager = ConversationManager(session)
    query_processor = QueryProcessor()
    context_manager = ContextManager()
    prompt_manager = PromptManager()
    llm_service = LLMService()
    
    return (
        conversation_manager,
        query_processor,
        context_manager,
        prompt_manager,
        llm_service
    )


# WebSocket Connection Manager
class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a WebSocket for a user."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a WebSocket for a user."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: int):
        """Send a message to all connections for a specific user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Connection might be closed, will be cleaned up on next disconnect
                    pass


connection_manager = ConnectionManager()


# REST API Endpoints
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """Create a new conversation."""
    try:
        conversation_manager = services[0]
        
        conversation = await conversation_manager.create_conversation(
            user_id=user_id,
            title=request.title,
            category=request.category,
            tags=request.tags
        )
        
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            user_id=conversation.user_id,
            status=conversation.status,
            category=conversation.category,
            tags=conversation.tags,
            is_favorite=conversation.is_favorite,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0,
            last_message_at=None
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = 1,
    per_page: int = 20,
    category: Optional[str] = None,
    status: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """List conversations for the current user."""
    try:
        conversation_manager = services[0]
        
        conversations = await conversation_manager.list_conversations(
            user_id=user_id,
            category=category,
            status=status,
            page=page,
            per_page=per_page
        )
        
        conversation_responses = []
        for conv in conversations:
            conversation_responses.append(ConversationResponse(
                id=conv.id,
                title=conv.title,
                user_id=conv.user_id,
                status=conv.status,
                category=conv.category,
                tags=conv.tags,
                is_favorite=conv.is_favorite,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(conv.messages) if hasattr(conv, 'messages') else 0,
                last_message_at=conv.updated_at
            ))
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total=len(conversation_responses),
            page=page,
            per_page=per_page,
            has_next=len(conversation_responses) == per_page,
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """Get a specific conversation by ID."""
    try:
        conversation_manager = services[0]
        
        conversation = await conversation_manager.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            user_id=conversation.user_id,
            status=conversation.status,
            category=conversation.category,
            tags=conversation.tags,
            is_favorite=conversation.is_favorite,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(conversation.messages) if hasattr(conversation, 'messages') else 0,
            last_message_at=conversation.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    page: int = 1,
    per_page: int = 50,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """Get messages for a conversation."""
    try:
        conversation_manager = services[0]
        
        # Verify user has access to conversation
        conversation = await conversation_manager.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = await conversation_manager.get_conversation_messages(
            conversation_id=conversation_id,
            page=page,
            per_page=per_page
        )
        
        message_responses = []
        for msg in messages:
            message_responses.append(MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                user_id=msg.user_id,
                content=msg.content,
                message_type=msg.message_type,
                role=msg.role,
                created_at=msg.created_at,
                is_ai_response=msg.role == "assistant",
                processing_time_ms=msg.processing_time_ms,
                model_used=msg.model_used
            ))
        
        return {
            "messages": message_responses,
            "total": len(message_responses),
            "page": page,
            "per_page": per_page,
            "conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    request: SendMessageRequest,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """Send a message to a conversation."""
    try:
        (conversation_manager, query_processor, 
         context_manager, prompt_manager, llm_service) = services
        
        # Verify user has access to conversation
        conversation = await conversation_manager.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Add user message
        user_message = await conversation_manager.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=request.content,
            role="user",
            message_type=request.message_type
        )
        
        # Process query and generate AI response
        start_time = datetime.now()
        
        # 1. Process the query
        processed_query = query_processor.process_query(request.content)
        
        # 2. Get conversation context
        conversation_context = await conversation_manager.get_conversation_context(
            conversation_id, max_messages=10
        )
        
        # 3. Build context window (simulate document retrieval for now)
        mock_chunks = [
            {"content": "User authentication documentation content...", "score": 0.9},
            {"content": "JWT token validation guidelines...", "score": 0.8}
        ]
        context_window = context_manager.build_context_window(
            query=processed_query,
            chunks=mock_chunks,
            conversation_context=conversation_context
        )
        
        # 4. Build prompt
        prompt_data = prompt_manager.build_rag_prompt(
            query=processed_query,
            context_window=context_window,
            conversation_context=conversation_context
        )
        
        # 5. Generate AI response
        ai_response = await llm_service.generate_response(
            prompt=prompt_data.full_prompt,
            model_params=prompt_data.model_params
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 6. Add AI message
        ai_message = await conversation_manager.add_message(
            conversation_id=conversation_id,
            user_id=None,  # AI message
            content=ai_response.content,
            role="assistant",
            message_type="text",
            processing_time_ms=int(processing_time),
            model_used=ai_response.model_used
        )
        
        # Send WebSocket notification
        await connection_manager.send_personal_message(
            json.dumps({
                "type": "new_message",
                "conversation_id": conversation_id,
                "message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "role": ai_message.role,
                    "created_at": ai_message.created_at.isoformat()
                }
            }),
            user_id
        )
        
        return MessageResponse(
            id=ai_message.id,
            conversation_id=ai_message.conversation_id,
            user_id=ai_message.user_id,
            content=ai_message.content,
            message_type=ai_message.message_type,
            role=ai_message.role,
            created_at=ai_message.created_at,
            is_ai_response=True,
            processing_time_ms=ai_message.processing_time_ms,
            model_used=ai_message.model_used
        )
        
    except HTTPException:
        raise
    except AIError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except ProcessingError as e:
        raise HTTPException(status_code=422, detail=f"Processing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


# Streaming Endpoints
@router.post("/conversations/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: int,
    request: SendMessageRequest,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """Send a message with streaming response."""
    
    async def generate_stream():
        try:
            (conversation_manager, query_processor, 
             context_manager, prompt_manager, llm_service) = services
            
            # Verify user has access to conversation
            conversation = await conversation_manager.get_conversation(conversation_id, user_id)
            if not conversation:
                yield f"data: {json.dumps({'type': 'error', 'content': 'Conversation not found'})}\n\n"
                return
            
            # Add user message
            user_message = await conversation_manager.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                content=request.content,
                role="user",
                message_type=request.message_type
            )
            
            yield f"data: {json.dumps({'type': 'user_message_added', 'message_id': user_message.id})}\n\n"
            
            # Process query
            yield f"data: {json.dumps({'type': 'status', 'content': 'Processing query...'})}\n\n"
            processed_query = query_processor.process_query(request.content)
            
            # Get context
            yield f"data: {json.dumps({'type': 'status', 'content': 'Building context...'})}\n\n"
            conversation_context = await conversation_manager.get_conversation_context(
                conversation_id, max_messages=10
            )
            
            # Mock document retrieval
            mock_chunks = [
                {"content": "User authentication documentation content...", "score": 0.9},
                {"content": "JWT token validation guidelines...", "score": 0.8}
            ]
            context_window = context_manager.build_context_window(
                query=processed_query,
                chunks=mock_chunks,
                conversation_context=conversation_context
            )
            
            # Build prompt
            prompt_data = prompt_manager.build_rag_prompt(
                query=processed_query,
                context_window=context_window,
                conversation_context=conversation_context
            )
            
            # Stream AI response
            yield f"data: {json.dumps({'type': 'status', 'content': 'Generating response...'})}\n\n"
            
            full_response = ""
            async for chunk in llm_service.stream_response(
                prompt=prompt_data.full_prompt,
                model_params=prompt_data.model_params
            ):
                full_response += chunk.content
                yield f"data: {json.dumps({'type': 'message_chunk', 'content': chunk.content})}\n\n"
            
            # Save AI message
            ai_message = await conversation_manager.add_message(
                conversation_id=conversation_id,
                user_id=None,
                content=full_response,
                role="assistant",
                message_type="text"
            )
            
            yield f"data: {json.dumps({'type': 'message_complete', 'message_id': ai_message.id, 'conversation_id': conversation_id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# WebSocket Endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """WebSocket endpoint for real-time chat."""
    await connection_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            
            elif message_data.get("type") == "typing":
                # Broadcast typing indicator to other connections for the same user
                await connection_manager.send_personal_message(
                    json.dumps({
                        "type": "typing",
                        "conversation_id": message_data.get("conversation_id"),
                        "user_id": user_id
                    }),
                    user_id
                )
            
            # Add more message type handlers as needed
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket, user_id)


# Health check endpoint
@router.get("/health")
async def chat_health_check():
    """Health check endpoint for chat services."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "chat_api": "operational",
            "websocket": "operational",
            "rag_system": "operational"
        }
    }