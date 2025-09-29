"""
Document Processing Service - Simplified Version
Handles secure file upload, processing, and storage pipeline
Works with existing database models
"""

import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.models.chat_models import Document, DocumentChunk, ProcessingStatus
from .text_extractor import text_extractor
from .vector_store import vector_store
from ...shared.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Complete document processing pipeline with security validation
    """
    
    def __init__(self):
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 100  # Character overlap between chunks
    
    async def process_uploaded_file(
        self, 
        file_content: bytes, 
        filename: str,
        user_id: int,
        thread_id: int,
        session: AsyncSession
    ) -> Document:
        """
        Process uploaded file through complete pipeline
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            user_id: ID of user uploading file
            thread_id: Chat thread ID
            session: Database session
            
        Returns:
            Document: Processed document entity
        """
        try:
            logger.info(f"Starting document processing for {filename}")
            
            # Generate content hash for deduplication
            content_hash = hashlib.sha256(file_content).hexdigest()
            checksum = hashlib.md5(file_content).hexdigest()
            
            # Extract text first
            extraction_result = await self._extract_text_async(file_content, filename)
            
            # Create document record with all required fields
            document = Document(
                thread_id=thread_id,
                user_id=user_id,
                filename=filename,
                original_filename=filename,
                mime_type=extraction_result['mime_type'],
                file_extension=f".{extraction_result['file_type']}",
                size_bytes=extraction_result['file_size'],
                document_type=extraction_result['file_type'],
                content_hash=content_hash,
                checksum=checksum,
                virus_scan_status="passed",  # Simplified for now
                processing_status=ProcessingStatus.PROCESSING.value,
                extracted_text=extraction_result['text'],
                word_count=extraction_result['word_count'],
                character_count=extraction_result['character_count'],
                storage_path=f"/documents/{content_hash}/{filename}",  # Virtual path
                processing_started_at=datetime.utcnow()
            )
            
            # Add to session
            session.add(document)
            await session.flush()  # Get the ID
            
            # Create text chunks
            chunks = await self._create_chunks(
                extraction_result['text'], 
                document.id
            )
            
            # Save chunks
            for chunk in chunks:
                session.add(chunk)
            
            # Step 5: Generate embeddings and store in vector database
            try:
                await self._generate_embeddings(document.id, chunks)
                document.embedding_status = "completed"
                logger.info(f"Generated embeddings for {len(chunks)} chunks")
            except Exception as embedding_error:
                logger.warning(f"Embedding generation failed: {embedding_error}")
                document.embedding_status = "failed"
            
            # Update document status
            document.processing_status = ProcessingStatus.COMPLETED.value
            document.processing_completed_at = datetime.utcnow()
            document.chunk_count = len(chunks)
            
            await session.commit()
            
            logger.info(f"Successfully processed document {filename} with {len(chunks)} chunks and embeddings")
            return document
            
        except Exception as e:
            logger.error(f"Document processing failed for {filename}: {str(e)}")
            await session.rollback()
            raise DocumentProcessingError(f"Document processing failed: {str(e)}")
    
    async def _extract_text_async(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Async wrapper for text extraction
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, text_extractor.extract_text, file_content, filename)
    
    async def _create_chunks(self, text: str, document_id: int) -> List[DocumentChunk]:
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
            
            # Generate hash for chunk
            chunk_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
            
            # Create chunk entity
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk_index,
                content=chunk_text.strip(),
                content_hash=chunk_hash,
                start_position=start,
                end_position=end,
                character_count=len(chunk_text.strip()),
                word_count=len(chunk_text.strip().split()),
                token_count=len(chunk_text.strip().split())  # Simplified token count
            )
            
            chunks.append(chunk)
            chunk_index += 1
            
            # Move start position with overlap
            if end == len(text):
                break
            
            start = end - self.chunk_overlap
        
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        return chunks
    
    async def _generate_embeddings(self, document_id: int, chunks: List[DocumentChunk]) -> None:
        """
        Generate embeddings for document chunks and store in vector database
        
        Args:
            document_id: Document ID
            chunks: List of document chunks
        """
        try:
            # Ensure vector store is initialized
            if not vector_store.initialized:
                await vector_store.initialize()
            
            # Convert chunks to format expected by vector store
            chunk_data = []
            for chunk in chunks:
                chunk_dict = {
                    'id': chunk.id,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content,
                    'character_count': chunk.character_count,
                    'word_count': chunk.word_count,
                    'start_position': chunk.start_position,
                    'end_position': chunk.end_position
                }
                chunk_data.append(chunk_dict)
            
            # Add chunks to vector store
            embeddings_count = await vector_store.add_document_chunks(document_id, chunk_data)
            
            logger.info(f"Generated {embeddings_count} embeddings for document {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for document {document_id}: {str(e)}")
            raise DocumentProcessingError(f"Embedding generation failed: {str(e)}")
    
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
    
    async def search_documents(
        self, 
        query: str, 
        user_id: int, 
        session: AsyncSession,
        n_results: int = 5,
        document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents using semantic similarity
        
        Args:
            query: Search query
            user_id: User ID (for access control)
            session: Database session
            n_results: Number of results to return
            document_ids: Optional filter by specific documents
            
        Returns:
            List of search results with document context
        """
        try:
            # Ensure vector store is initialized
            if not vector_store.initialized:
                await vector_store.initialize()
            
            # If document_ids not provided, get all user's documents
            if document_ids is None:
                user_docs = await self.get_user_documents(user_id, session, limit=100)
                document_ids = [doc.id for doc in user_docs]
            
            # Search similar chunks
            similar_chunks = await vector_store.search_similar_chunks(
                query=query,
                n_results=n_results,
                document_ids=document_ids
            )
            
            # Enrich results with document information
            enriched_results = []
            
            for chunk in similar_chunks:
                doc_id = chunk['metadata']['document_id']
                
                # Get document details
                document = await self.get_document_status(doc_id, session)
                
                if document and document.user_id == user_id:  # Access control check
                    result = {
                        'chunk_content': chunk['content'],
                        'similarity_score': chunk['similarity_score'],
                        'document_id': doc_id,
                        'document_filename': document.filename,
                        'chunk_index': chunk['metadata']['chunk_index'],
                        'start_position': chunk['metadata']['start_position'],
                        'end_position': chunk['metadata']['end_position']
                    }
                    enriched_results.append(result)
            
            logger.info(f"Semantic search for '{query}' returned {len(enriched_results)} results")
            return enriched_results
            
        except Exception as e:
            logger.error(f"Document search failed: {str(e)}")
            raise DocumentProcessingError(f"Document search failed: {str(e)}")
    
    async def get_document_status(self, document_id: int, session: AsyncSession) -> Optional[Document]:
        """
        Get document processing status
        
        Args:
            document_id: Document ID
            session: Database session
            
        Returns:
            Document: Document with current status
        """
        result = await session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()
    
    async def get_user_documents(self, user_id: int, session: AsyncSession, limit: int = 50) -> List[Document]:
        """
        Get all documents for a user
        
        Args:
            user_id: User ID
            session: Database session
            limit: Maximum number of documents to return
            
        Returns:
            List[Document]: User's documents
        """
        result = await session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def delete_document(self, document_id: int, user_id: int, session: AsyncSession) -> bool:
        """
        Delete document and all associated chunks
        
        Args:
            document_id: Document ID
            user_id: User ID (for ownership verification)
            session: Database session
            
        Returns:
            bool: True if deletion successful
        """
        # Verify ownership
        document = await self.get_document_status(document_id, session)
        if not document or document.user_id != user_id:
            raise DocumentProcessingError("Document not found or access denied")
        
        # Delete embeddings from vector store first
        try:
            if vector_store.initialized:
                deleted_embeddings = await vector_store.delete_document_chunks(document_id)
                logger.info(f"Deleted {deleted_embeddings} embeddings for document {document_id}")
        except Exception as e:
            logger.warning(f"Failed to delete embeddings: {str(e)}")
        
        # Delete chunks first (cascading should handle this, but being explicit)
        await session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        
        # Delete document
        await session.delete(document)
        await session.commit()
        
        logger.info(f"Deleted document {document_id} and all chunks")
        return True


# Global document processor instance
document_processor = DocumentProcessor()