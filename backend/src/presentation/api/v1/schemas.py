"""
Excel API Schemas

Pydantic schemas for Excel API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class ExcelDocumentResponse(BaseModel):
    """Response schema for Excel document."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    filename: str
    original_filename: str
    file_size: int
    sheet_count: int
    total_rows: int
    total_columns: int
    status: str
    error_message: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None


class ExcelSheetResponse(BaseModel):
    """Response schema for Excel sheet."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    document_id: int
    sheet_name: str
    sheet_index: int
    row_count: int
    column_count: int
    columns: Optional[List[str]] = None
    column_types: Optional[Dict[str, str]] = None
    statistics: Optional[Dict[str, Any]] = None
    semantic_types: Optional[Dict[str, str]] = None
    key_columns: Optional[List[str]] = None
    has_missing_values: bool
    missing_percentage: int
    duplicate_rows: int
    created_at: datetime
    updated_at: datetime


class ExcelSheetPreviewResponse(BaseModel):
    """Response schema for sheet preview data."""
    
    sheet_name: str
    rows: int
    columns: int
    column_names: List[str]
    data: List[Dict[str, Any]]
    preview_size: int


class ExcelQueryRequest(BaseModel):
    """Request schema for creating a query."""
    
    query_text: str = Field(..., min_length=1, max_length=1000)
    target_sheet: Optional[str] = None


class ExcelQueryResponse(BaseModel):
    """Response schema for Excel query."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    document_id: int
    user_id: int
    query_text: str
    query_type: Optional[str] = None
    target_sheet: Optional[str] = None
    generated_code: Optional[str] = None
    code_explanation: Optional[str] = None
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime
    executed_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    """Response schema for list of documents."""
    
    documents: List[ExcelDocumentResponse]
    total: int
    skip: int
    limit: int


class CacheStatsResponse(BaseModel):
    """Response schema for cache statistics."""
    
    entry_count: int
    size_mb: float
    max_size_mb: float
    utilization_percentage: float
