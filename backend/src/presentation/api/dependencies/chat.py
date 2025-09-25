"""
Chat Dependencies

This module provides dependency injection functions for chat-related
endpoints in the FastAPI application.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.repositories import (
    ChatThreadRepository,
    ChatMessageRepository,
    DocumentRepository
)
from backend.src.infrastructure.repositories.chat_repositories import (
    SQLAChatThreadRepository,
    SQLAChatMessageRepository,
    SQLADocumentRepository
)
from backend.src.application.services.chat_service import ChatService
from backend.src.infrastructure.database.config import get_database_session
from backend.src.presentation.api.dependencies.auth import get_current_user


async def get_thread_repository(
    session: Annotated[AsyncSession, Depends(get_database_session)]
) -> ChatThreadRepository:
    """
    Dependency that provides a ChatThreadRepository instance.
    """
    return SQLAChatThreadRepository(session)


async def get_message_repository(
    session: Annotated[AsyncSession, Depends(get_database_session)]
) -> ChatMessageRepository:
    """
    Dependency that provides a ChatMessageRepository instance.
    """
    return SQLAChatMessageRepository(session)


async def get_document_repository(
    session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DocumentRepository:
    """
    Dependency that provides a DocumentRepository instance.
    """
    return SQLADocumentRepository(session)


async def get_chat_service(
    thread_repo: Annotated[ChatThreadRepository, Depends(get_thread_repository)],
    message_repo: Annotated[ChatMessageRepository, Depends(get_message_repository)],
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository)]
) -> ChatService:
    """
    Dependency that provides a ChatService instance.
    """
    return ChatService(
        thread_repository=thread_repo,
        message_repository=message_repo,
        document_repository=document_repo
    )
