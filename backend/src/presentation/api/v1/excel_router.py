"""
Excel API Router

FastAPI endpoints for Excel document management and analysis.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
import os

from ....infrastructure.database.database import get_db_session
from ....application.use_cases.excel import ExcelService
from ....presentation.api.dependencies.auth import get_current_user
from ....application.dto import UserDTO
from ....domain.models.excel_models import ExcelDocument
from .schemas import (
    ExcelDocumentResponse,
    ExcelSheetResponse,
    ExcelSheetPreviewResponse,
    ExcelQueryRequest,
    ExcelQueryResponse,
    DocumentListResponse,
    CacheStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/excel", tags=["Excel"])

# Initialize service with Anthropic API key from environment
excel_service = ExcelService(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)


@router.post("/upload", response_model=ExcelDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_excel_file(
    file: UploadFile = File(...),
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Upload an Excel file for analysis.
    
    - **file**: Excel file (.xlsx, .xls, .xlsm)
    - **Returns**: Document metadata and processing status
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Check file size (50MB limit)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 50MB limit"
            )
        
        # Upload and process
        document = await excel_service.upload_document(
            file=file.file,
            filename=file.filename,
            user_id=current_user.id,
            db=db
        )
        
        # Debug: Check document attributes
        logger.info(f"Document object type: {type(document)}")
        logger.info(f"Document attributes: {dir(document)}")
        logger.info(f"Has total_rows: {hasattr(document, 'total_rows')}")
        if hasattr(document, 'total_rows'):
            logger.info(f"total_rows value: {document.total_rows}")
        
        return ExcelDocumentResponse.from_orm(document)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def get_user_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all Excel documents for the current user.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **Returns**: List of documents
    """
    try:
        documents = await excel_service.get_user_documents(
            user_id=current_user.id,
            db=db,
            skip=skip,
            limit=limit
        )
        
        return DocumentListResponse(
            documents=[ExcelDocumentResponse.from_orm(doc) for doc in documents],
            total=len(documents),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/{document_id}", response_model=ExcelDocumentResponse)
async def get_document(
    document_id: int,
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific Excel document by ID.
    
    - **document_id**: Document ID
    - **Returns**: Document metadata
    """
    try:
        document = await excel_service.get_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return ExcelDocumentResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.get("/{document_id}/sheets", response_model=List[ExcelSheetResponse])
async def get_document_sheets(
    document_id: int,
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all sheets for a document.
    
    - **document_id**: Document ID
    - **Returns**: List of sheets with metadata
    """
    try:
        sheets = await excel_service.get_document_sheets(
            document_id=document_id,
            user_id=current_user.id,
            db=db
        )
        
        return [ExcelSheetResponse.from_orm(sheet) for sheet in sheets]
        
    except Exception as e:
        logger.error(f"Error getting sheets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sheets"
        )


@router.get("/{document_id}/sheets/{sheet_name}/preview", response_model=ExcelSheetPreviewResponse)
async def get_sheet_preview(
    document_id: int,
    sheet_name: str,
    rows: int = Query(10, ge=1, le=100),
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get a preview of sheet data.
    
    - **document_id**: Document ID
    - **sheet_name**: Sheet name
    - **rows**: Number of rows to preview (1-100)
    - **Returns**: Preview data
    """
    try:
        preview = await excel_service.get_sheet_preview(
            document_id=document_id,
            sheet_name=sheet_name,
            user_id=current_user.id,
            db=db,
            rows=rows
        )
        
        return ExcelSheetPreviewResponse(**preview)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preview"
        )


@router.get("/{document_id}/example-questions")
async def get_example_questions(
    document_id: int,
    sheet_name: Optional[str] = None,
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate intelligent example questions based on the document's columns.
    
    - **document_id**: Document ID
    - **sheet_name**: Optional sheet name (uses first sheet if not provided)
    - **Returns**: List of example questions tailored to the document
    """
    try:
        questions = await excel_service.generate_example_questions(
            document_id=document_id,
            sheet_name=sheet_name,
            user_id=current_user.id,
            db=db
        )
        
        return {"questions": questions}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating example questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate example questions"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete an Excel document.
    
    - **document_id**: Document ID
    - **Returns**: No content on success
    """
    try:
        deleted = await excel_service.delete_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.post("/{document_id}/query", response_model=ExcelQueryResponse, status_code=status.HTTP_201_CREATED)
async def create_query(
    document_id: int,
    query_request: ExcelQueryRequest,
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a natural language query for analysis.
    
    - **document_id**: Document ID
    - **query_request**: Query details
    - **Returns**: Created query with pending status
    """
    try:
        # Verify document exists
        document = await excel_service.get_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Save query
        query = await excel_service.save_query(
            document_id=document_id,
            user_id=current_user.id,
            query_text=query_request.query_text,
            target_sheet=query_request.target_sheet,
            db=db
        )
        
        return ExcelQueryResponse.from_orm(query)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create query"
        )


@router.post("/{document_id}/queries/{query_id}/execute", response_model=ExcelQueryResponse)
async def execute_query(
    document_id: int,
    query_id: int,
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Execute a saved natural language query.
    
    - **document_id**: Document ID
    - **query_id**: Query ID to execute
    - **Returns**: Query with execution results
    """
    try:
        # Execute query
        query = await excel_service.execute_query(
            query_id=query_id,
            user_id=current_user.id,
            db=db
        )
        
        return ExcelQueryResponse.from_orm(query)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute query: {str(e)}"
        )


@router.get("/{document_id}/queries", response_model=List[ExcelQueryResponse])
async def get_query_history(
    document_id: int,
    limit: int = Query(20, ge=1, le=100),
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get query history for a document.
    
    - **document_id**: Document ID
    - **limit**: Maximum number of queries to return
    - **Returns**: List of queries
    """
    try:
        queries = await excel_service.get_query_history(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
            limit=limit
        )
        
        return [ExcelQueryResponse.from_orm(query) for query in queries]
        
    except Exception as e:
        logger.error(f"Error getting queries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queries"
        )


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    current_user: UserDTO = Depends(get_current_user)
):
    """
    Get cache statistics (admin/debugging).
    
    - **Returns**: Cache utilization stats
    """
    try:
        stats = excel_service.get_cache_stats()
        return CacheStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache stats"
        )


@router.post("/cache/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cache(
    current_user: UserDTO = Depends(get_current_user)
):
    """
    Clear the sheet cache (admin/debugging).
    
    - **Returns**: No content on success
    """
    try:
        excel_service.clear_cache()
        return None
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )


@router.get("/optimizer/metrics")
async def get_optimizer_metrics(
    current_user: UserDTO = Depends(get_current_user)
):
    """
    Get query optimizer performance metrics.
    
    - **Returns**: Optimizer metrics including cache hit rate, query patterns
    """
    try:
        metrics = excel_service.get_optimizer_metrics()
        cache_stats = excel_service.get_optimizer_cache_stats()
        
        return {
            **metrics,
            "cache_details": cache_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting optimizer metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get optimizer metrics"
        )


@router.post("/optimizer/cache/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_query_cache(
    current_user: UserDTO = Depends(get_current_user)
):
    """
    Clear the query result cache.
    
    - **Returns**: Number of entries cleared
    """
    try:
        count = excel_service.clear_query_cache()
        logger.info(f"Cleared {count} query cache entries")
        return None
        
    except Exception as e:
        logger.error(f"Error clearing query cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear query cache"
        )
