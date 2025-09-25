"""
Enhanced Chat Service

Service for chat functionality using enhanced immutable entities.
"""

from dataclasses import replace
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncIterator

from ...domain.entities.chat.chat_entities import (
    ChatThread,
    ChatMessage,
    Document,
    MessageRole,
    MessageStatus,
    MessageType,
    ThreadStatus,
    ThreadCategory,
    ProcessingStatus,
    DocumentType
)
from ...domain.chat.repositories import (
    ChatThreadRepository,
    ChatMessageRepository,
    DocumentRepository
)
from .ai_service import ai_service
from ...infrastructure.ai.config import AIModel
from ...domain.ai.interfaces import AIMessage, MessageRole as AIMessageRole


class EnhancedChatService:
    """Enhanced service for chat functionality using immutable entities."""
    
    def __init__(
        self,
        thread_repository: ChatThreadRepository,
        message_repository: ChatMessageRepository,
        document_repository: DocumentRepository
    ):
        self.thread_repository = thread_repository
        self.message_repository = message_repository
        self.document_repository = document_repository
    
    def _convert_chat_messages_to_ai_messages(self, messages: List[ChatMessage]) -> List[AIMessage]:
        """Convert ChatMessage objects to AIMessage objects."""
        ai_messages = []
        
        for msg in messages:
            # Map MessageRole to AIMessageRole
            if msg.role == MessageRole.USER:
                ai_role = AIMessageRole.USER
            elif msg.role == MessageRole.ASSISTANT:
                ai_role = AIMessageRole.ASSISTANT
            elif msg.role == MessageRole.SYSTEM:
                ai_role = AIMessageRole.SYSTEM
            else:
                ai_role = AIMessageRole.USER  # Default fallback
                
            ai_messages.append(AIMessage(
                role=ai_role,
                content=msg.content,
                metadata={
                    "message_id": msg.id,
                    "thread_id": msg.thread_id,
                    "user_id": msg.user_id,
                    "message_type": msg.message_type.value if msg.message_type else None,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
            ))
        
        return ai_messages
    
    async def create_thread(
        self, 
        user_id: int, 
        title: str,
        category: ThreadCategory = ThreadCategory.GENERAL,
        tags: Optional[List[str]] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> ChatThread:
        """Create a new chat thread."""
        thread = ChatThread(
            user_id=user_id,
            title=title,
            category=category,
            tags=tags or [],
            meta_data=meta_data or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return await self.thread_repository.create(thread)
    
    async def get_thread(self, thread_id: int) -> Optional[ChatThread]:
        """Get a thread by ID."""
        return await self.thread_repository.get_by_id(thread_id)
    
    async def update_thread(
        self,
        thread_id: int,
        title: Optional[str] = None,
        status: Optional[ThreadStatus] = None,
        category: Optional[ThreadCategory] = None,
        tags: Optional[List[str]] = None,
        is_favorite: Optional[bool] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatThread]:
        """Update a thread with new information."""
        thread = await self.thread_repository.get_by_id(thread_id)
        if not thread:
            return None
            
        update_fields: Dict[str, Any] = {
            'updated_at': datetime.utcnow()
        }
        
        if title is not None:
            update_fields['title'] = title
        if status is not None:
            update_fields['status'] = status
        if category is not None:
            update_fields['category'] = category
        if tags is not None:
            update_fields['tags'] = tags
        if is_favorite is not None:
            update_fields['is_favorite'] = is_favorite
        if meta_data is not None:
            update_fields['meta_data'] = {**thread.meta_data, **meta_data}
            
        updated_thread = replace(thread, **update_fields)
        return await self.thread_repository.update(updated_thread)
    
    async def get_user_threads(
        self, 
        user_id: int,
        status: Optional[ThreadStatus] = None,
        category: Optional[ThreadCategory] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatThread]:
        """Get threads for a user with filtering options."""
        return await self.thread_repository.get_by_user(
            user_id=user_id,
            status=status,
            category=category,
            limit=limit,
            offset=offset
        )
    
    async def create_message(
        self, 
        thread_id: int,
        user_id: int,
        content: str,
        role: MessageRole = MessageRole.USER,
        message_type: MessageType = MessageType.TEXT,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Create a new chat message."""
        message = ChatMessage(
            thread_id=thread_id,
            user_id=user_id,
            content=content,
            role=role,
            message_type=message_type,
            status=MessageStatus.COMPLETED,
            meta_data=meta_data or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created_message = await self.message_repository.create(message)
        
        # Update thread's last_message_at and message count
        thread = await self.thread_repository.get_by_id(thread_id)
        if thread:
            updated_thread = replace(
                thread,
                last_message_at=datetime.utcnow(),
                message_count=thread.message_count + 1,
                updated_at=datetime.utcnow()
            )
            await self.thread_repository.update(updated_thread)
            
        return created_message
    
    async def get_thread_messages(
        self, 
        thread_id: int,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[ChatMessage]:
        """Get messages for a thread."""
        return await self.message_repository.get_by_thread(
            thread_id=thread_id,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted
        )
    
    async def update_message(
        self,
        message_id: int,
        content: Optional[str] = None,
        status: Optional[MessageStatus] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatMessage]:
        """Update a message with new information."""
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            return None
            
        update_fields: Dict[str, Any] = {
            'updated_at': datetime.utcnow()
        }
        
        if content is not None:
            update_fields['content'] = content
            update_fields['edit_count'] = message.edit_count + 1
            if message.original_content is None:
                update_fields['original_content'] = message.content
                
        if status is not None:
            update_fields['status'] = status
            
        if meta_data is not None:
            update_fields['meta_data'] = {**message.meta_data, **meta_data}
            
        updated_message = replace(message, **update_fields)
        return await self.message_repository.update(updated_message)
    
    async def create_ai_response(
        self,
        thread_id: int,
        user_id: int,
        ai_provider: str,
        ai_model: str,
        initial_content: str = ""
    ) -> ChatMessage:
        """Create an AI response message for streaming."""
        message = ChatMessage(
            thread_id=thread_id,
            user_id=user_id,
            content=initial_content,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.AI_RESPONSE,
            status=MessageStatus.PROCESSING,
            ai_provider=ai_provider,
            ai_model=ai_model,
            meta_data={"is_streaming": True},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return await self.message_repository.create(message)
    
    async def update_streaming_response(
        self,
        message_id: int,
        content: str,
        is_final: bool = False,
        tokens_used: int = 0,
        processing_time_ms: int = 0
    ) -> Optional[ChatMessage]:
        """Update a streaming AI response."""
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            return None
            
        update_fields: Dict[str, Any] = {
            'content': content,
            'updated_at': datetime.utcnow()
        }
        
        if is_final:
            update_fields.update({
                'status': MessageStatus.COMPLETED,
                'tokens_used': tokens_used,
                'processing_time_ms': processing_time_ms,
                'processed_at': datetime.utcnow(),
                'meta_data': {**message.meta_data, 'is_streaming': False}
            })
        
        updated_message = replace(message, **update_fields)
        return await self.message_repository.update(updated_message)
    
    async def search_messages(
        self,
        thread_id: int,
        query: str,
        limit: int = 20
    ) -> List[ChatMessage]:
        """Search messages within a thread."""
        return await self.message_repository.search_messages(
            thread_id=thread_id,
            query=query,
            limit=limit
        )
    
    async def get_conversation_context(
        self,
        thread_id: int,
        max_tokens: int = 4000
    ) -> List[ChatMessage]:
        """Get conversation context for AI processing."""
        return await self.message_repository.get_conversation_context(
            thread_id=thread_id,
            max_tokens=max_tokens
        )
    
    async def create_document(
        self,
        thread_id: int,
        user_id: int,
        filename: str,
        original_filename: str,
        mime_type: str,
        file_extension: str,
        size_bytes: int,
        storage_path: str,
        content_hash: str,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create a new document record."""
        # Determine document type from extension
        doc_type = DocumentType.TXT  # Default
        ext_lower = file_extension.lower()
        if ext_lower in ['.pdf']:
            doc_type = DocumentType.PDF
        elif ext_lower in ['.docx', '.doc']:
            doc_type = DocumentType.DOCX
        elif ext_lower in ['.md']:
            doc_type = DocumentType.MD
        elif ext_lower in ['.html', '.htm']:
            doc_type = DocumentType.HTML
        elif ext_lower in ['.jpg', '.jpeg', '.png', '.gif']:
            doc_type = DocumentType.IMAGE
        
        document = Document(
            thread_id=thread_id,
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            mime_type=mime_type,
            file_extension=file_extension,
            size_bytes=size_bytes,
            document_type=doc_type,
            storage_path=storage_path,
            content_hash=content_hash,
            processing_status=ProcessingStatus.PENDING,
            meta_data=meta_data or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created_document = await self.document_repository.create(document)
        
        # Update thread's document count
        thread = await self.thread_repository.get_by_id(thread_id)
        if thread:
            updated_thread = replace(
                thread,
                document_count=thread.document_count + 1,
                updated_at=datetime.utcnow()
            )
            await self.thread_repository.update(updated_thread)
            
        return created_document
    
    async def get_thread_documents(self, thread_id: int) -> List[Document]:
        """Get all documents for a thread."""
        return await self.document_repository.get_by_thread(thread_id)
    
    async def update_document_processing(
        self,
        document_id: int,
        status: ProcessingStatus,
        extracted_text: Optional[str] = None,
        chunk_count: Optional[int] = None,
        vector_store_id: Optional[str] = None,
        processing_error: Optional[str] = None
    ) -> Optional[Document]:
        """Update document processing status and results."""
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            return None
            
        update_fields: Dict[str, Any] = {
            'processing_status': status,
            'updated_at': datetime.utcnow()
        }
        
        if extracted_text is not None:
            update_fields['extracted_text'] = extracted_text
        if chunk_count is not None:
            update_fields['chunk_count'] = chunk_count
        if vector_store_id is not None:
            update_fields['vector_store_id'] = vector_store_id
        if processing_error is not None:
            update_fields['processing_error'] = processing_error
            
        if status == ProcessingStatus.COMPLETED:
            update_fields['processing_completed_at'] = datetime.utcnow()
            
        updated_document = replace(document, **update_fields)
        return await self.document_repository.update(updated_document)
    
    async def get_searchable_documents(self, thread_id: int) -> List[Document]:
        """Get documents ready for semantic search."""
        return await self.document_repository.get_searchable_documents(thread_id)
    
    async def search_documents(
        self,
        user_id: int,
        query: str,
        document_types: Optional[List[str]] = None
    ) -> List[Document]:
        """Search documents by content."""
        return await self.document_repository.search_documents(
            user_id=user_id,
            query=query,
            document_types=document_types
        )
    
    async def delete_message(self, message_id: int) -> bool:
        """Soft delete a message."""
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            return False
            
        updated_message = replace(
            message,
            deleted_at=datetime.utcnow(),
            status=MessageStatus.DELETED,
            updated_at=datetime.utcnow()
        )
        
        await self.message_repository.update(updated_message)
        return True
    
    async def archive_thread(self, thread_id: int, user_id: int) -> bool:
        """Archive a thread."""
        return await self.thread_repository.archive_thread(thread_id, user_id)
    
    async def restore_thread(self, thread_id: int, user_id: int) -> bool:
        """Restore an archived thread."""
        return await self.thread_repository.restore_thread(thread_id, user_id)
    
    async def delete_thread(self, thread_id: int) -> bool:
        """Delete a thread."""
        return await self.thread_repository.delete(thread_id)
    
    async def create_user_message(
        self,
        thread_id: int,
        user_id: int,
        content: str,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Create a user message (alias for create_message)."""
        return await self.create_message(
            thread_id=thread_id,
            user_id=user_id,
            content=content,
            role=MessageRole.USER,
            message_type=MessageType.TEXT,
            meta_data=meta_data
        )
    
    async def stream_assistant_response(
        self,
        thread_id: int,
        user_id: int,
        ai_provider: str = "openai",
        ai_model: str = "gpt-3.5-turbo"
    ):
        """Stream an assistant response (placeholder implementation)."""
        # This is a placeholder - would integrate with actual AI provider
        assistant_message = await self.create_ai_response(
            thread_id=thread_id,
            user_id=user_id,
            ai_provider=ai_provider,
            ai_model=ai_model,
            initial_content=""
        )
        
        # Simulate streaming response
        full_response = "This is a simulated AI response. In a real implementation, this would stream from the AI provider."
        
        for i, char in enumerate(full_response):
            content_so_far = full_response[:i+1]
            is_final = i == len(full_response) - 1
            
            if assistant_message.id is not None:
                await self.update_streaming_response(
                    message_id=assistant_message.id,
                    content=content_so_far,
                    is_final=is_final,
                    tokens_used=len(content_so_far.split()) if is_final else 0
                )
            
            yield {
                "content": char,
                "message_id": assistant_message.id,
                "is_complete": is_final
            }
    
    # AI Integration Methods
    async def generate_ai_response(
        self,
        thread_id: int,
        user_id: int,
        user_message: str,
        model: Optional[AIModel] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatMessage:
        """Generate a real AI response for a user message."""
        # Create user message
        user_msg = await self.create_message(
            thread_id=thread_id,
            user_id=user_id,
            content=user_message,
            role=MessageRole.USER,
            message_type=MessageType.TEXT
        )
        
        # Get conversation context
        messages = await self.get_thread_messages(
            thread_id=thread_id,
            limit=20  # Last 20 messages for context
        )
        
        try:
            # Convert ChatMessage to AIMessage
            ai_messages = self._convert_chat_messages_to_ai_messages(messages)
            
            # Generate AI response
            response = await ai_service.generate_chat_response(
                messages=ai_messages,
                model_name=model.value if model else None
            )
            
            # Create AI message
            ai_message = await self.create_message(
                thread_id=thread_id,
                user_id=user_id,  # System user for AI
                content=response.content,
                role=MessageRole.ASSISTANT,
                message_type=MessageType.AI_RESPONSE,
                meta_data={
                    "ai_provider": response.provider.value,
                    "ai_model": response.model,
                    "ai_tokens": response.tokens_used,
                    "ai_cost": (response.metadata or {}).get("cost", 0.0),
                    "processing_time_ms": response.processing_time_ms
                }
            )
            
            return ai_message
            
        except Exception as e:
            # Create error message
            error_message = await self.create_message(
                thread_id=thread_id,
                user_id=user_id,
                content=f"Sorry, I encountered an error: {str(e)}",
                role=MessageRole.ASSISTANT,
                message_type=MessageType.SYSTEM_NOTIFICATION,
                meta_data={"error": str(e)}
            )
            return error_message
    
    async def generate_ai_streaming_response(
        self,
        thread_id: int,
        user_id: int,
        user_message: str,
        model: Optional[AIModel] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate a real streaming AI response for a user message."""
        # Create user message
        user_msg = await self.create_message(
            thread_id=thread_id,
            user_id=user_id,
            content=user_message,
            role=MessageRole.USER,
            message_type=MessageType.TEXT
        )
        
        # Create initial AI response placeholder
        ai_message = await self.create_ai_response(
            thread_id=thread_id,
            user_id=user_id,
            ai_provider=model.value if model else "openai",
            ai_model=model.value if model else "gpt-4o-mini",
            initial_content=""
        )
        
        # Get conversation context
        messages = await self.get_thread_messages(
            thread_id=thread_id,
            limit=20  # Last 20 messages for context
        )
        
        full_content = ""
        total_tokens = 0
        
        try:
            # Convert ChatMessage to AIMessage
            ai_messages = self._convert_chat_messages_to_ai_messages(messages)
            
            # Generate streaming response
            async for chunk in ai_service.generate_chat_streaming_response(
                messages=ai_messages,
                model_name=model.value if model else None
            ):
                full_content += chunk.delta
                
                # Update the AI message in database
                if ai_message.id is not None:
                    await self.update_streaming_response(
                        message_id=ai_message.id,
                        content=full_content,
                        is_final=chunk.is_complete,
                        tokens_used=chunk.tokens_used if chunk.is_complete else 0
                    )
                
                # Yield streaming chunk to client
                yield {
                    "content": chunk.delta,
                    "full_content": full_content,
                    "message_id": ai_message.id,
                    "is_complete": chunk.is_complete,
                    "tokens_used": chunk.tokens_used if chunk.is_complete else 0
                }
                
                if chunk.is_complete:
                    total_tokens = chunk.tokens_used
                    break
                    
        except Exception as e:
            # Update with error message
            error_content = f"Sorry, I encountered an error: {str(e)}"
            if ai_message.id is not None:
                await self.update_streaming_response(
                    message_id=ai_message.id,
                    content=error_content,
                    is_final=True,
                    tokens_used=0
                )
            
            yield {
                "content": error_content,
                "full_content": error_content,
                "message_id": ai_message.id,
                "is_complete": True,
                "tokens_used": 0,
                "error": str(e)
            }
    
    async def get_ai_conversation_summary(self, thread_id: int, max_length: int = 200) -> str:
        """Generate an AI summary of the conversation."""
        messages = await self.get_thread_messages(thread_id=thread_id)
        
        if not messages:
            return "Empty conversation"
        
        try:
            # Convert ChatMessage to AIMessage
            ai_messages = self._convert_chat_messages_to_ai_messages(messages)
            
            return await ai_service.get_conversation_summary(
                messages=ai_messages,
                max_length=max_length
            )
        except Exception as e:
            return f"Could not generate summary: {str(e)}"