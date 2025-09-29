"""
Document Upload API Endpoints
Secure file upload with admin-only access and processing
"""

from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ....infrastructure.database.database import get_db_session
from ....infrastructure.document.simple_document_processor import document_processor, DocumentProcessingError
from ....infrastructure.database.models.chat_models import Document, ChatThread
from ....presentation.api.dependencies.auth import get_current_user, require_admin


logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post("/upload", response_model=dict)
async def upload_document(
    thread_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(require_admin)  # Admin only
):
    """
    Upload and process a document (Admin only)
    
    Args:
        thread_id: Optional chat thread ID to associate document with (will create/find one if not provided)
        file: Uploaded file
        session: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Dict with document processing results
    """
    try:
        logger.info(f"Document upload attempt by user {current_user.id}: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        
        # Ensure filename is not None
        safe_filename = file.filename if file.filename is not None else "unnamed_file"
        
        # Validate upload (extract role value as string)
        role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        await document_processor.validate_upload(
            file_content, 
            safe_filename, 
            role_value
        )
        
        # Handle thread_id - find existing or create new thread
        if thread_id is None:
            # Look for an existing thread for this user, or create a new one
            stmt = select(ChatThread).where(
                ChatThread.user_id == current_user.id
            ).order_by(ChatThread.created_at.desc()).limit(1)
            
            result = await session.execute(stmt)
            existing_thread = result.scalar_one_or_none()
            
            if existing_thread:
                thread_id = existing_thread.id
                logger.info(f"Using existing thread {thread_id} for user {current_user.id}")
            else:
                # Create a simple new thread for document uploads
                from datetime import datetime
                new_thread = ChatThread(
                    user_id=current_user.id,
                    title="Document Uploads",
                    category="general",
                    status="active",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    tags=[],
                    meta_data={},
                    message_count=0,
                    document_count=0,
                    total_tokens_used=0,
                    ai_configuration={}
                )
                session.add(new_thread)
                await session.commit()
                await session.refresh(new_thread)
                thread_id = new_thread.id
                logger.info(f"Created new document thread {thread_id} for user {current_user.id}")
        else:
            # Verify the provided thread exists and belongs to the user
            stmt = select(ChatThread).where(ChatThread.id == thread_id)
            result = await session.execute(stmt)
            existing_thread = result.scalar_one_or_none()
            
            if not existing_thread:
                raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
            
            if existing_thread.user_id != current_user.id:
                raise HTTPException(status_code=403, detail=f"Thread {thread_id} does not belong to current user")
        
        # Ensure thread_id is not None at this point
        assert thread_id is not None, "thread_id should not be None after thread handling"
        
        # Process the document
        document = await document_processor.process_uploaded_file(
            file_content=file_content,
            filename=safe_filename,
            user_id=current_user.id,
            thread_id=thread_id,
            session=session
        )
        
        return {
            "success": True,
            "message": "Document uploaded and processed successfully",
            "document": {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.document_type,
                "size_bytes": document.size_bytes,
                "word_count": document.word_count,
                "character_count": document.character_count,
                "chunk_count": document.chunk_count,
                "processing_status": document.processing_status,
                "created_at": document.created_at.isoformat()
            }
        }
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error during document upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Document upload failed")


@router.get("/status/{document_id}", response_model=dict)
async def get_document_status(
    document_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Get document processing status
    
    Args:
        document_id: Document ID
        session: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with document status information
    """
    try:
        document = await document_processor.get_document_status(document_id, session)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership or admin access
        if document.user_id != current_user.id and current_user.role != 'ADMIN':
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "document": {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.document_type,
                "size_bytes": document.size_bytes,
                "processing_status": document.processing_status,
                "word_count": document.word_count,
                "character_count": document.character_count,
                "chunk_count": document.chunk_count,
                "created_at": document.created_at.isoformat(),
                "processing_started_at": document.processing_started_at.isoformat() if document.processing_started_at else None,
                "processing_completed_at": document.processing_completed_at.isoformat() if document.processing_completed_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document status")


@router.get("/my-documents", response_model=dict)
async def get_my_documents(
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Get current user's documents
    
    Args:
        limit: Maximum number of documents to return
        session: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with list of user's documents
    """
    try:
        documents = await document_processor.get_user_documents(current_user.id, session, limit)
        
        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.document_type,
                    "size_bytes": doc.size_bytes,
                    "processing_status": doc.processing_status,
                    "word_count": doc.word_count,
                    "character_count": doc.character_count,
                    "chunk_count": doc.chunk_count,
                    "created_at": doc.created_at.isoformat(),
                    "thread_id": doc.thread_id
                }
                for doc in documents
            ],
            "total": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error getting user documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get documents")


@router.delete("/{document_id}", response_model=dict)
async def delete_document(
    document_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Delete a document (Owner or Admin only)
    
    Args:
        document_id: Document ID to delete
        session: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with deletion confirmation
    """
    try:
        # Check if user can delete (owner or admin)
        document = await document_processor.get_document_status(document_id, session)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.user_id != current_user.id and current_user.role != 'ADMIN':
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete the document
        await document_processor.delete_document(document_id, document.user_id, session)
        
        return {
            "success": True,
            "message": f"Document {document.filename} deleted successfully"
        }
        
    except HTTPException:
        raise
    except DocumentProcessingError as e:
        logger.error(f"Document deletion error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get("/validate-upload", response_model=dict)
async def validate_file_upload(
    current_user = Depends(require_admin)
):
    """
    Check if current user can upload files (Admin only endpoint)
    
    Args:
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Dict with upload permission status
    """
    return {
        "can_upload": True,
        "user_role": current_user.role,
        "supported_types": ["PDF", "DOCX", "TXT", "HTML"],
        "max_file_size": "10 MB",
        "message": "User authorized for document upload"
    }


@router.post("/search", response_model=dict)
async def search_documents(
    query: str = Form(...),
    n_results: int = Form(5),
    document_ids: Optional[List[int]] = Form(None),
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Search documents using semantic similarity
    
    Args:
        query: Search query text
        n_results: Number of results to return (default: 5)
        document_ids: Optional list of specific document IDs to search within
        session: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with search results
    """
    try:
        logger.info(f"Semantic search by user {current_user.id}: '{query[:50]}...'")
        
        # Perform semantic search
        results = await document_processor.search_documents(
            query=query,
            user_id=current_user.id,
            session=session,
            n_results=n_results,
            document_ids=document_ids
        )
        
        return {
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except DocumentProcessingError as e:
        logger.error(f"Document search error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error during document search: {str(e)}")
        raise HTTPException(status_code=500, detail="Document search failed")


@router.get("/vector-store/status", response_model=dict)
async def get_vector_store_status(
    current_user = Depends(get_current_user)
):
    """
    Get vector store status and statistics
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict with vector store information
    """
    try:
        from ....infrastructure.document.vector_store import vector_store
        
        # Get health check
        health = await vector_store.health_check()
        
        # Get statistics if initialized
        stats = {}
        if vector_store.initialized:
            stats = await vector_store.get_collection_stats()
        
        return {
            "health": health,
            "stats": stats,
            "user_id": current_user.id
        }
        
    except Exception as e:
        logger.error(f"Error getting vector store status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get vector store status")


@router.post("/vector-store/initialize", response_model=dict)
async def initialize_vector_store(
    current_user = Depends(require_admin)  # Admin only
):
    """
    Initialize vector store (Admin only)
    
    Args:
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Dict with initialization status
    """
    try:
        from ....infrastructure.document.vector_store import vector_store
        
        if vector_store.initialized:
            return {
                "success": True,
                "message": "Vector store already initialized",
                "status": "already_initialized"
            }
        
        # Initialize vector store
        await vector_store.initialize()
        
        return {
            "success": True,
            "message": "Vector store initialized successfully",
            "status": "initialized"
        }
        
    except DocumentProcessingError as e:
        logger.error(f"Vector store initialization error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error during vector store initialization: {str(e)}")
        raise HTTPException(status_code=500, detail="Vector store initialization failed")