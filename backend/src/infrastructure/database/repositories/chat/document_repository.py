"""
Document Repository for chat system document storage and retrieval
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.chat_models import Document, DocumentChunk
from ..base_repository import BaseRepository


class DocumentRepository(BaseRepository):
    """Repository for document storage and retrieval"""
    
    async def create(self, document: Document, session: AsyncSession) -> Document:
        """
        Create a new document
        """
        session.add(document)
        await session.flush()
        return document
    
    async def update(self, document: Document, session: AsyncSession) -> Document:
        """
        Update an existing document
        """
        session.add(document)
        await session.flush()
        return document
    
    async def create_chunk(self, chunk: DocumentChunk, session: AsyncSession) -> DocumentChunk:
        """
        Create a new document chunk
        """
        session.add(chunk)
        await session.flush()
        return chunk
    
    async def get_document_by_id(self, document_id: str, session: AsyncSession) -> Optional[Document]:
        """
        Get document by ID
        """
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_document_chunks(self, document_id: str, session: AsyncSession) -> List[DocumentChunk]:
        """
        Get all chunks for a document
        """
        stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    async def delete_document(self, document_id: str, session: AsyncSession) -> bool:
        """
        Delete a document and all its chunks
        """
        # Delete all chunks first
        chunk_stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        await session.execute(chunk_stmt)
        
        # Then delete the document
        doc_stmt = delete(Document).where(Document.id == document_id)
        result = await session.execute(doc_stmt)
        
        return result.rowcount > 0
    
    async def get_documents_by_thread(
        self, thread_id: str, session: AsyncSession, limit: int = 100, offset: int = 0
    ) -> List[Document]:
        """
        Get documents for a thread with pagination
        """
        stmt = (
            select(Document)
            .where(Document.thread_id == thread_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_documents_by_user(
        self, user_id: str, session: AsyncSession, limit: int = 100, offset: int = 0
    ) -> List[Document]:
        """
        Get documents for a user with pagination
        """
        stmt = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
