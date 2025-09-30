"""
Chat API Router

FastAPI router for chat endpoints including REST API and WebSocket support.
Integrates with the RAG system for intelligent responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from ...shared.exceptions import (
    ValidationError, 
    NotFoundError, 
    ProcessingError,
    AIError
)
from ...infrastructure.database.database import get_db_session
from ...infrastructure.ai.conversation_manager import ConversationManager
from ...infrastructure.ai.query_processor import QueryProcessor, Message
from ...infrastructure.ai.context_manager import ContextManager
from ...infrastructure.ai.prompt_manager import PromptManager
from ...infrastructure.ai.llm_service import LLMService
from ...infrastructure.database.models import ChatThread, ChatMessage, UserModel
from ...infrastructure.database.models.chat_models import Document
from ...presentation.api.dependencies.auth import get_current_active_user

# LangChain integration imports
from ...infrastructure.langchain.simple_langchain_service import SimpleLangChainRAGService
from ...infrastructure.document.vector_store import VectorStore
from ...infrastructure.document.document_processor import DocumentProcessor


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
    chat_mode: Optional[str] = Field("general", description="Chat mode: 'general' for normal AI chat, 'rag' for document-based chat")
    selected_documents: Optional[List[int]] = Field(None, description="List of selected document IDs for context-specific queries")


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


# Initialize logger
logger = logging.getLogger(__name__)

# Router and dependency setup
router = APIRouter(tags=["chat"])


async def get_current_user_id(
    current_user = Depends(get_current_active_user)
) -> int:
    """Get current user ID from authentication context."""
    return current_user.id


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


async def get_langchain_service(
    session: AsyncSession = Depends(get_db_session)
) -> SimpleLangChainRAGService:
    """
    Get LangChain RAG service with all custom components wrapped for compliance.
    
    This dependency provides a LangChain-compatible interface while using
    our optimized custom components underneath for maximum performance.
    """
    # Initialize our custom components (keep the performance)
    vector_store = VectorStore()
    llm_service = LLMService()
    context_manager = ContextManager()
    document_processor = DocumentProcessor(db_session=session)
    
    # Create LangChain service that wraps our custom components
    langchain_service = SimpleLangChainRAGService(
        vector_store=vector_store,
        llm_service=llm_service,
        context_manager=context_manager,
        document_processor=document_processor,
        memory_k=5,  # Conversation memory window
        retriever_k=5  # Document retrieval count
    )
    
    return langchain_service


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
        
        logger.info(f"Creating conversation for user {user_id} with title: {request.title}")
        
        conversation = await conversation_manager.create_conversation(
            user_id=user_id,
            title=request.title,
            category=request.category,
            tags=request.tags
        )
        
        logger.info(f"Conversation created successfully: {conversation.id}")
        
        response = ConversationResponse(
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
        
        logger.info(f"Response model created successfully")
        return response
        
    except ValidationError as e:
        logger.error(f"Validation error creating conversation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = 1,
    per_page: int = 20,
    category: Optional[str] = None,
    status: Optional[str] = None,
    include_archived: bool = False,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """List conversations for the current user. Excludes archived/deleted conversations by default."""
    try:
        conversation_manager = services[0]
        
        conversations = await conversation_manager.list_conversations(
            user_id=user_id,
            category=category,
            status=status,
            page=page,
            per_page=per_page,
            include_archived=include_archived
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
                message_count=conv.message_count,
                last_message_at=conv.last_message_at
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
            message_count=conversation.message_count,
            last_message_at=conversation.last_message_at
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
                conversation_id=msg.thread_id,  # Use thread_id instead of conversation_id
                user_id=msg.user_id,
                content=msg.content,
                message_type=msg.message_type,
                role=msg.role,
                created_at=msg.created_at,
                is_ai_response=msg.role == "assistant",
                processing_time_ms=msg.processing_time_ms,
                model_used=msg.ai_model
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


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """Delete a conversation thread and all its messages."""
    try:
        conversation_manager = services[0]
        
        logger.info(f"Deleting conversation {conversation_id} for user {user_id}")
        
        # Verify the conversation belongs to the current user
        conversation = await conversation_manager.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Delete the conversation (this should cascade delete all messages)
        success = await conversation_manager.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete conversation"
            )
        
        logger.info(f"Conversation {conversation_id} deleted successfully")
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


@router.patch("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """Archive a conversation thread (soft delete)."""
    try:
        conversation_manager = services[0]
        
        logger.info(f"Archiving conversation {conversation_id} for user {user_id}")
        
        # Soft delete the conversation
        success = await conversation_manager.soft_delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or could not be archived"
            )
        
        logger.info(f"Conversation {conversation_id} archived successfully")
        
        return {"message": "Conversation archived successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to archive conversation")


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    request: SendMessageRequest,
    user_id: int = Depends(get_current_user_id),
    services: tuple = Depends(get_chat_services)
):
    """Send a message to a conversation."""
    try:
        logger.info(f"🔍 DEBUG: Received message request - Content: {request.content}")
        logger.info(f"🔍 DEBUG: Selected documents: {request.selected_documents}")
        logger.info(f"🔍 DEBUG: Chat mode: {request.chat_mode}")
        logger.info(f"🔍 DEBUG: Request model fields: {request.model_fields}")
        
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
        logger.info("Step 1: Processing query")
        processed_query = await query_processor.process_query(request.content, user_id)
        logger.info(f"Processed query: {processed_query}")
        
        # 2. Get conversation context
        logger.info("Step 2: Getting conversation context")
        conversation_context = await conversation_manager.get_conversation_context(
            conversation_id, max_messages=10
        )
        logger.info(f"Conversation context: {len(conversation_context.messages)} messages")
        
        # 3. Build context window (retrieve actual documents)
        logger.info("Step 3: Building context window with real documents")
        
        # Use the existing session from the services dependency
        # Get database session through the get_chat_services function
        session_gen = get_db_session()
        session = await session_gen.__anext__()
        
        try:
            # Query documents directly from the database for this conversation
            from sqlalchemy import text
            
            # Build query based on whether specific documents are selected
            if request.selected_documents:
                logger.info(f"Using selected documents: {request.selected_documents}")
                # Document IDs are now integers, no conversion needed
                try:
                    doc_ids = request.selected_documents
                    placeholders = ','.join([':doc_id_' + str(i) for i in range(len(doc_ids))])
                    # Allow cross-thread document access for selected documents - user can reference any of their documents
                    query = text(f"""
                        SELECT id, filename, extracted_text, word_count, created_at 
                        FROM chat_documents 
                        WHERE user_id = :user_id 
                        AND id IN ({placeholders})
                        AND processing_status = 'completed'
                        AND extracted_text IS NOT NULL
                        ORDER BY created_at DESC
                        LIMIT 10
                    """)
                    params = {"user_id": user_id}
                    for i, doc_id in enumerate(doc_ids):
                        params[f"doc_id_{i}"] = doc_id
                    result = await session.execute(query, params)
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid document IDs provided: {request.selected_documents}, error: {e}")
                    # Fall back to all user documents if IDs are invalid
                    query = text("""
                        SELECT id, filename, extracted_text, word_count, created_at 
                        FROM chat_documents 
                        WHERE user_id = :user_id 
                        AND processing_status = 'completed'
                        AND extracted_text IS NOT NULL
                        LIMIT 10
                    """)
                    result = await session.execute(query, {"user_id": user_id})
            else:
                # Use all available documents if none selected
                query = text("""
                    SELECT id, filename, extracted_text, word_count, created_at 
                    FROM chat_documents 
                    WHERE thread_id = :thread_id 
                    AND processing_status = 'completed'
                    AND extracted_text IS NOT NULL
                    LIMIT 10
                """)
                result = await session.execute(query, {"thread_id": conversation_id})
            
            documents = result.fetchall()
            
            logger.info(f"Found {len(documents)} documents for conversation {conversation_id}")
            
            # Create chunks from document content
            retrieved_chunks = []
            for doc in documents:
                if doc.extracted_text:  # doc.extracted_text is index 2
                    # Create a chunk object with the required attributes
                    class DocumentChunk:
                        def __init__(self, doc_id, filename, content):
                            self.id = doc_id
                            self.content = content[:2000] if len(content) > 2000 else content
                            self.chunk_index = 0
                            # Create a simple document-like object
                            self.document = type('Document', (), {
                                'filename': filename,
                                'created_at': doc.created_at
                            })()
                    
                    chunk = DocumentChunk(doc.id, doc.filename, doc.extracted_text)
                    retrieved_chunks.append(chunk)
            
            logger.info(f"Created {len(retrieved_chunks)} chunks from documents")
            
            # Build context window with real document content or fallback to mock
            if retrieved_chunks:
                context_window = await context_manager.build_context_window(
                    retrieved_chunks=retrieved_chunks,
                    query=processed_query
                )
            else:
                # Fallback to empty context if no documents found
                logger.info("No documents found, using empty context")
                context_window = await context_manager.build_context_window(
                    retrieved_chunks=[],
                    query=processed_query
                )
        finally:
            await session.close()
        logger.info("Context window built successfully")
        
        # Convert conversation messages to Message objects
        message_objects = []
        if conversation_context and conversation_context.messages:
            for msg_dict in conversation_context.messages:
                message_objects.append(Message(
                    role=msg_dict["role"],
                    content=msg_dict["content"],
                    timestamp=datetime.fromisoformat(msg_dict["timestamp"]) if isinstance(msg_dict["timestamp"], str) else msg_dict["timestamp"],
                    message_id=str(msg_dict["id"])
                ))
        
        # 4. Build prompt based on chat mode  
        logger.info(f"Step 4: Building prompt for {request.chat_mode} mode")
        
        if request.chat_mode == "rag":
            # Use RAG mode with document context
            prompt_data = await prompt_manager.build_rag_prompt(
                query=request.content,  # Original query string
                processed_query=processed_query,  # ProcessedQuery object
                context_window=context_window,
                chat_history=message_objects
            )
        else:
            # Use general chat mode - just the user query with conversation history
            prompt_data = request.content
            
        logger.info("Prompt built successfully")
        
        # 5. Generate AI response
        try:
            logger.info(f"Step 5: Generating AI response for {request.chat_mode} mode")
            
            if request.chat_mode == "rag":
                # RAG mode - use document context
                ai_response = await llm_service.generate_response(
                    query=prompt_data,  # Use the formatted RAG prompt
                    context_window=context_window,
                    conversation_history=message_objects,
                    model=None,  # Let LLM service use default
                    temperature=None,  # Let LLM service use default
                    max_tokens=None  # Let LLM service use default
                )
            else:
                # General chat mode - use simpler approach
                ai_response = await llm_service.generate_general_response(
                    query=request.content,
                    conversation_history=message_objects,
                    model=None,
                    temperature=0.7,  # Slightly more creative for general chat
                    max_tokens=None
                )
            
            logger.info(f"AI response generated successfully: {ai_response.content[:100]}...")
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}", exc_info=True)
            raise
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 6. Add AI message
        logger.info("Step 6: Saving AI message")
        ai_message = await conversation_manager.add_message(
            conversation_id=conversation_id,
            user_id=user_id,  # Use current user ID for AI messages to avoid FK constraint
            content=ai_response.content,
            role="assistant",
            message_type="text",
            processing_time_ms=int(processing_time),
            model_used=ai_response.model
        )
        logger.info(f"AI message saved successfully: ID {ai_message.id}")
        
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
            conversation_id=ai_message.thread_id,  # Use thread_id instead of conversation_id
            user_id=ai_message.user_id,
            content=ai_message.content,
            message_type=ai_message.message_type,
            role=ai_message.role,
            created_at=ai_message.created_at,
            is_ai_response=True,
            processing_time_ms=ai_message.processing_time_ms,
            model_used=ai_message.ai_model
        )
        
    except HTTPException:
        raise
    except AIError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except ProcessingError as e:
        raise HTTPException(status_code=422, detail=f"Processing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/conversations/{conversation_id}/messages/langchain", response_model=MessageResponse)
async def send_message_langchain(
    conversation_id: int,
    request: SendMessageRequest,
    user_id: int = Depends(get_current_user_id),
    langchain_service: SimpleLangChainRAGService = Depends(get_langchain_service),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Send a message using LangChain RAG pipeline.
    
    This endpoint provides the same functionality as the standard message endpoint
    but uses LangChain framework for RAG processing while maintaining the same
    performance through our custom component wrappers.
    """
    try:
        logger.info(f"🔗 LangChain endpoint: Processing message for conversation {conversation_id}")
        
        # Create conversation manager
        conversation_manager = ConversationManager(session)
        
        # Verify user has access to conversation
        conversation = await conversation_manager.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Add user message to conversation
        user_message = await conversation_manager.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=request.content,
            role="user",
            message_type=request.message_type or "text"
        )
        logger.info(f"✅ User message saved: ID {user_message.id}")
        
        # Generate AI response using LangChain service
        start_time = datetime.now()
        
        logger.info("🔗 Using LangChain RAG pipeline for response generation")
        
        # Use LangChain service (which internally uses our custom components)
        langchain_response = await langchain_service.chat(
            message=request.content,
            thread_id=conversation_id,
            session_id=f"user_{user_id}_conv_{conversation_id}",
            selected_documents=request.selected_documents
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"✅ LangChain response generated in {processing_time:.2f}ms")
        logger.info(f"📊 LangChain metadata: {langchain_response.get('metadata', {})}")
        
        # Add AI message to conversation
        ai_message = await conversation_manager.add_message(
            conversation_id=conversation_id,
            user_id=user_id,  # Use current user ID for AI messages
            content=langchain_response["answer"],
            role="assistant",
            message_type="text",
            processing_time_ms=int(processing_time),
            model_used="langchain_rag_pipeline"
        )
        logger.info(f"✅ AI message saved: ID {ai_message.id}")
        
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
                },
                "langchain_metadata": {
                    "framework": "langchain_wrapper",
                    "documents_used": len(langchain_response.get("source_documents", [])),
                    "context_chunks": len(langchain_response.get("context_used", [])),
                    "chain_type": langchain_response.get("chain_type", "custom_rag_chain")
                }
            }),
            user_id
        )
        
        return MessageResponse(
            id=ai_message.id,
            conversation_id=ai_message.thread_id,
            user_id=ai_message.user_id,
            content=ai_message.content,
            message_type=ai_message.message_type,
            role=ai_message.role,
            created_at=ai_message.created_at,
            is_ai_response=True,
            processing_time_ms=ai_message.processing_time_ms,
            model_used=ai_message.ai_model
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ LangChain endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"LangChain processing failed: {str(e)}")


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
            
            # Real document retrieval
            yield f"data: {json.dumps({'type': 'status', 'content': 'Retrieving documents...'})}\n\n"
            
            # Get database session to retrieve documents
            session_gen = get_db_session()
            session = await session_gen.__anext__()
            
            try:
                # Query documents directly from the database for this conversation
                from sqlalchemy import text
                
                query = text("""
                    SELECT id, filename, extracted_text, word_count, created_at 
                    FROM chat_documents 
                    WHERE thread_id = :thread_id 
                    AND processing_status = 'completed'
                    AND extracted_text IS NOT NULL
                    LIMIT 10
                """)
                result = await session.execute(query, {"thread_id": conversation_id})
                documents = result.fetchall()
                
                logger.info(f"Found {len(documents)} documents for conversation {conversation_id}")
                
                # Create chunks from document content
                retrieved_chunks = []
                for doc in documents:
                    if doc.extracted_text:  # doc.extracted_text is index 2
                        chunk_data = {
                            "content": doc.extracted_text[:2000] if len(doc.extracted_text) > 2000 else doc.extracted_text,
                            "score": 0.9,  # Default relevance score
                            "document_name": doc.filename
                        }
                        retrieved_chunks.append(chunk_data)
                
                logger.info(f"Created {len(retrieved_chunks)} chunks from documents")
                
                # Use real document chunks or fallback to empty
                context_window = context_manager.build_context_window(
                    query=processed_query,
                    chunks=retrieved_chunks,
                    conversation_context=conversation_context
                )
            finally:
                await session.close()
            
            # Build prompt
            prompt_data = prompt_manager.build_rag_prompt(
                query=processed_query,
                context_window=context_window,
                conversation_context=conversation_context
            )
            
            # Stream AI response
            yield f"data: {json.dumps({'type': 'status', 'content': 'Generating response...'})}\n\n"
            
            # Map model params if present
            model_params = getattr(prompt_data, "model_params", {}) or {}
            
            full_response = ""
            async for chunk in llm_service.stream_response(
                query=request.content,
                context_window=context_window,
                conversation_history=conversation_context.get("history", []) if conversation_context else [],
                model=model_params.get("model"),
                temperature=model_params.get("temperature")
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


@router.get("/health/langchain")
async def langchain_health_check(
    langchain_service: SimpleLangChainRAGService = Depends(get_langchain_service)
):
    """Health check endpoint for LangChain integration."""
    try:
        # Get LangChain system information
        chain_info = langchain_service.get_chain_info()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "framework": "langchain_wrapper",
            "langchain_integration": chain_info,
            "custom_components": {
                component: str(type(comp).__name__)
                for component, comp in langchain_service.get_custom_components().items()
            },
            "services": {
                "langchain_rag_pipeline": "operational",
                "custom_vector_store": "operational",
                "custom_llm_service": "operational",
                "custom_context_manager": "operational",
                "custom_document_processor": "operational"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "framework": "langchain_wrapper"
        }