"""
Document Processing Service
Handles secure file upload, processing, and storage pipeline
"""

import uuid
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.chat_models import Document, DocumentChunk, ProcessingStatus as DocumentProcessingStatus
from .text_extractor import text_extractor

# Import necessary for document repository
import os
from pathlib import Path
import sys

# Create a DocumentRepository adapter class
class DocumentRepository:
    """Document repository adapter for document processing"""
    
    def __init__(self, db_session=None):
        """Initialize with optional session"""
        self.db_session = db_session
        
    async def create(self, document, session):
        """Create a document"""
        session.add(document)
        return document
    
    async def update(self, document, session):
        """Update a document"""
        session.add(document)
        return document
    
    async def create_chunk(self, chunk, session):
        """Create a document chunk"""
        session.add(chunk)
        return chunk
    
    async def get_by_id(self, document_id, session):
        """Get document by ID"""
        from sqlalchemy import select
        from ..database.models.chat_models import Document
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_by_user_id(self, user_id, session, limit=50):
        """Get documents by user ID"""
        from sqlalchemy import select
        from ..database.models.chat_models import Document
        stmt = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
        
    async def delete(self, document_id, session):
        """Delete document by ID"""
        from sqlalchemy import delete
        from ..database.models.chat_models import Document
        stmt = delete(Document).where(Document.id == document_id)
        await session.execute(stmt)
        return True
        
    async def delete_chunks_by_document_id(self, document_id, session):
        """Delete document chunks by document ID"""
        from sqlalchemy import delete
        from ..database.models.chat_models import DocumentChunk
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        await session.execute(stmt)
        return True
    
    async def get_session(self):
        """Get database session as async context manager"""
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def session_context():
            yield self.db_session
            
        return session_context()

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Custom exception for document processing errors"""
    pass


class DocumentProcessor:
    """
    Complete document processing pipeline with security validation
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 100  # Character overlap between chunks
        # Initialize the document repository
        self.document_repository = DocumentRepository(db_session)
    
    async def process_uploaded_file(
        self, 
        file_content: bytes, 
        filename: str,
        user_id: str,
        thread_id: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> Document:
        """
        Process uploaded file through complete pipeline
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            user_id: ID of user uploading file
            thread_id: Optional chat thread ID
            session: Database session
            
        Returns:
            Document: Processed document entity
        """
        document_id = str(uuid.uuid4())
        # Initialize document variable to avoid "possibly unbound" errors
        document = None
        
        try:
            logger.info(f"Starting document processing for {filename} (ID: {document_id})")
            
            # Create initial document record
            document = Document(
                id=document_id,
                filename=filename,
                original_filename=filename,
                mime_type="application/octet-stream",  # Default, will update later
                file_extension=filename.split('.')[-1] if '.' in filename else '',
                size_bytes=len(file_content),
                document_type="unknown",  # Will update later
                content_hash=hashlib.sha256(file_content).hexdigest(),
                checksum=hashlib.md5(file_content).hexdigest(),
                user_id=user_id,
                thread_id=thread_id,
                processing_status=DocumentProcessingStatus.PROCESSING.value,
                storage_path=f"/uploads/{document_id}/{filename}",
                storage_provider="local",
                created_at=datetime.utcnow()
            )
            
            # Save initial document
            db_session_to_use = session if session else self.db_session
            await self.document_repository.create(document, db_session_to_use)
            
            # Step 1: Extract text
            extraction_result = await self._extract_text_async(file_content, filename)
            
            # Step 2: Update document with extraction results
            document.document_type = extraction_result['file_type']
            document.size_bytes = extraction_result['file_size']
            document.word_count = extraction_result['word_count']
            document.character_count = extraction_result['character_count']
            
            # Step 3: Create text chunks
            chunks = await self._create_chunks(
                extraction_result['text'], 
                document_id
            )
            
            # Step 4: Save chunks and update document
            db_session_to_use = session if session else self.db_session
            
            # Save chunks
            for chunk in chunks:
                await self.document_repository.create_chunk(chunk, db_session_to_use)
            
            # Update document status
            document.processing_status = DocumentProcessingStatus.COMPLETED.value
            document.processing_completed_at = datetime.utcnow()
            await self.document_repository.update(document, db_session_to_use)
            
            # Commit if we're using our own session
            if not session and db_session_to_use:
                await db_session_to_use.commit()
            
            logger.info(f"Successfully processed document {filename} with {len(chunks)} chunks")
            return document
            
        except Exception as e:
            logger.error(f"Document processing failed for {filename}: {str(e)}")
            
            # Update document status to failed
            try:
                # Only try to update if document was created successfully and is not None
                if document is not None:
                    document.processing_status = DocumentProcessingStatus.FAILED.value
                    document.processing_error = str(e)
                    
                    db_session_to_use = session if session else self.db_session
                    await self.document_repository.update(document, db_session_to_use)
                    
                    # Commit if we're using our own session
                    if not session and db_session_to_use:
                        await db_session_to_use.commit()
                        
            except Exception as update_error:
                logger.error(f"Failed to update document status: {str(update_error)}")
            
            raise DocumentProcessingError(f"Document processing failed: {str(e)}")
    
    async def _extract_text_async(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Async wrapper for text extraction
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, text_extractor.extract_text, file_content, filename)
    
    async def _create_chunks(self, text: str, document_id: str) -> List[DocumentChunk]:
        """
        Split document text into searchable chunks
        
        Args:
            text: Extracted text content
            document_id: Document ID
            
        Returns:
            List[DocumentChunk]: List of text chunks
        """
        chunks = []
        
        # Split text into chunks with overlap
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = min(start + self.chunk_size, len(text))
            
            # Extract chunk text
            chunk_text = text[start:end]
            
            # Skip empty chunks
            if not chunk_text.strip():
                start = end
                continue
            
            # Create chunk entity
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=chunk_index,
                content=chunk_text.strip(),
                character_count=len(chunk_text.strip()),
                word_count=len(chunk_text.strip().split()),
                start_index=start,
                end_index=end,
                created_at=datetime.utcnow()
            )
            
            chunks.append(chunk)
            chunk_index += 1
            
            # Move start position with overlap
            if end == len(text):
                break
            
            start = end - self.chunk_overlap
        
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        return chunks
    
    async def validate_upload(self, file_content: bytes, filename: str, user_role: str) -> bool:
        """
        Validate file upload against security requirements
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            user_role: User's role (must be ADMIN)
            
        Returns:
            bool: True if upload is valid
            
        Raises:
            DocumentProcessingError: If validation fails
        """
        # Check user permissions (admin only) - handle both uppercase and lowercase
        if user_role not in ['ADMIN', 'admin', 'SUPERADMIN', 'superadmin']:
            raise DocumentProcessingError("Document upload restricted to admin users only")
        
        # Validate filename
        if not filename or len(filename.strip()) == 0:
            raise DocumentProcessingError("Invalid filename")
        
        # Check for potentially dangerous filenames
        dangerous_patterns = ['..', '/', '\\', '<script', 'javascript:', 'data:']
        filename_lower = filename.lower()
        
        for pattern in dangerous_patterns:
            if pattern in filename_lower:
                raise DocumentProcessingError(f"Filename contains potentially dangerous pattern: {pattern}")
        
        # Validate file using text extractor
        if not text_extractor.validate_file(file_content, filename):
            raise DocumentProcessingError("File validation failed - unsupported type or corrupted")
        
        return True
    
    async def get_document_status(self, document_id: str) -> Optional[Document]:
        """
        Get document processing status
        
        Args:
            document_id: Document ID
            
        Returns:
            Document: Document with current status
        """
        return await self.document_repository.get_by_id(document_id, self.db_session)
    
    async def get_user_documents(self, user_id: str, limit: int = 50) -> List[Document]:
        """
        Get all documents for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of documents to return
            
        Returns:
            List[Document]: User's documents
        """
        return await self.document_repository.get_by_user_id(user_id, self.db_session, limit)
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        Delete document and all associated chunks
        
        Args:
            document_id: Document ID
            user_id: User ID (for ownership verification)
            
        Returns:
            bool: True if deletion successful
        """
        # Verify ownership
        document = await self.document_repository.get_by_id(document_id, self.db_session)
        if not document or document.user_id != user_id:
            raise DocumentProcessingError("Document not found or access denied")
        
        # Delete chunks first
        await self.document_repository.delete_chunks_by_document_id(document_id, self.db_session)
        
        # Delete document
        await self.document_repository.delete(document_id, self.db_session)
        await self.db_session.commit()
        
        logger.info(f"Deleted document {document_id} and all chunks")
        return True