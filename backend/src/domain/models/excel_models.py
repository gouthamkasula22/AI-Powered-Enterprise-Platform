"""
Excel Database Models

SQLAlchemy models for Excel document management.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List, Dict, Any
from ...infrastructure.database.config import Base


class ExcelDocument(Base):
    """Model for Excel documents."""
    
    __tablename__ = "excel_documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Metadata
    sheet_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_columns: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='uploaded')
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    sheets = relationship("ExcelSheet", back_populates="document", cascade="all, delete-orphan")
    queries = relationship("ExcelQuery", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExcelDocument(id={self.id}, filename='{self.filename}', user_id={self.user_id})>"


class ExcelSheet(Base):
    """Model for individual sheets within Excel documents."""
    
    __tablename__ = "excel_sheets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("excel_documents.id"), nullable=False, index=True)
    sheet_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sheet_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Data dimensions
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Schema and statistics (stored as JSON)
    columns: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    column_types: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    statistics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    semantic_types: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    key_columns: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Data quality
    has_missing_values: Mapped[bool] = mapped_column(Boolean, default=False)
    missing_percentage: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("ExcelDocument", back_populates="sheets")
    
    def __repr__(self):
        return f"<ExcelSheet(id={self.id}, sheet_name='{self.sheet_name}', document_id={self.document_id})>"


class ExcelQuery(Base):
    """Model for natural language queries on Excel documents."""
    
    __tablename__ = "excel_queries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("excel_documents.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Query details
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_sheet: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Generated code
    generated_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Execution
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='pending')
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    document = relationship("ExcelDocument", back_populates="queries")
    visualizations = relationship("ExcelVisualization", back_populates="query", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExcelQuery(id={self.id}, query_text='{self.query_text[:50]}...', status='{self.status}')>"


class ExcelVisualization(Base):
    """Model for visualizations generated from Excel data."""
    
    __tablename__ = "excel_visualizations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query_id: Mapped[int] = mapped_column(Integer, ForeignKey("excel_queries.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Visualization details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chart_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Data
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Image export (optional)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_format: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    query = relationship("ExcelQuery", back_populates="visualizations")
    
    def __repr__(self):
        return f"<ExcelVisualization(id={self.id}, title='{self.title}', chart_type='{self.chart_type}')>"
