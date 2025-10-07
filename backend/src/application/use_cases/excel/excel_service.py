"""
Excel Service

Orchestrates Excel document processing, analysis, and storage.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ....domain.models.excel_models import ExcelDocument, ExcelSheet, ExcelQuery
from ....infrastructure.excel import ExcelProcessor, DataProfiler, SheetManager, CodeExecutor
from .query_processor import QueryProcessor
from .query_optimizer import QueryOptimizer

logger = logging.getLogger(__name__)


class ExcelService:
    """Service for managing Excel documents and analysis."""
    
    def __init__(
        self,
        upload_dir: str = "uploads/excel",
        cache_ttl_minutes: int = 30,
        cache_max_size_mb: int = 100,
        anthropic_api_key: Optional[str] = None
    ):
        """
        Initialize Excel service.
        
        Args:
            upload_dir: Directory for storing uploaded files
            cache_ttl_minutes: Cache TTL in minutes
            cache_max_size_mb: Maximum cache size in MB
            anthropic_api_key: Anthropic API key for query processing
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        self.processor = ExcelProcessor()
        self.profiler = DataProfiler()
        self.sheet_manager = SheetManager(
            cache_ttl_minutes=cache_ttl_minutes,
            cache_max_size_mb=cache_max_size_mb
        )
        self.code_executor = CodeExecutor()
        self.query_optimizer = QueryOptimizer()
        
        # Initialize query processor if API key provided
        if anthropic_api_key:
            self.query_processor = QueryProcessor(
                anthropic_api_key=anthropic_api_key,
                sheet_manager=self.sheet_manager
            )
        else:
            self.query_processor = None
            logger.warning("Query processor not initialized - no Anthropic API key provided")
    
    async def upload_document(
        self,
        file: BinaryIO,
        filename: str,
        user_id: int,
        db: AsyncSession
    ) -> ExcelDocument:
        """
        Upload and process an Excel document.
        
        Args:
            file: File object to upload
            filename: Original filename
            user_id: ID of user uploading the file
            db: Database session
            
        Returns:
            Created ExcelDocument instance
            
        Raises:
            ValueError: If file is invalid
        """
        # Validate file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ['.xlsx', '.xls', '.xlsm']:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{user_id}_{timestamp}_{filename}"
        file_path = self.upload_dir / unique_filename
        
        # Save file
        try:
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file, f)
            
            file_size = file_path.stat().st_size
            
            # Create database record
            document = ExcelDocument(
                user_id=user_id,
                filename=unique_filename,
                original_filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                mime_type=self._get_mime_type(file_ext),
                status='processing',
                sheet_count=0,
                total_rows=0,
                total_columns=0
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # Process document in background
            try:
                await self._process_document(document, db)
            except Exception as e:
                logger.error(f"Error processing document {document.id}: {str(e)}")
                document.status = 'error'
                document.error_message = str(e)
                await db.commit()
                await db.refresh(document)
                raise
            
            return document
            
        except Exception as e:
            # Clean up file on error
            if file_path.exists():
                file_path.unlink()
            raise
    
    async def _process_document(
        self,
        document: ExcelDocument,
        db: AsyncSession
    ) -> None:
        """
        Process an Excel document and extract metadata.
        
        Args:
            document: ExcelDocument to process
            db: Database session
        """
        try:
            # Process with ExcelProcessor
            metadata = await self.processor.process_file(
                document.file_path,
                document.user_id
            )
            
            # Update document metadata
            document.sheet_count = len(metadata['sheets'])
            document.total_rows = metadata['total_rows']
            document.total_columns = metadata['total_columns']
            
            # Process each sheet
            for sheet_meta in metadata['sheets']:
                # Load sheet data
                df = self.sheet_manager.load_sheet(
                    document.file_path,
                    sheet_meta['sheet_name']
                )
                
                # Generate statistics
                stats = self.profiler.generate_statistics(df)
                semantic_types = self.profiler.detect_data_types(df)
                key_columns = self.profiler.identify_key_columns(df)
                
                # Create sheet record
                sheet = ExcelSheet(
                    document_id=document.id,
                    sheet_name=sheet_meta['sheet_name'],
                    sheet_index=sheet_meta['sheet_index'],
                    row_count=sheet_meta['row_count'],
                    column_count=sheet_meta['column_count'],
                    columns=sheet_meta['columns'],
                    column_types=sheet_meta['dtypes'],
                    statistics=stats,
                    semantic_types=semantic_types,
                    key_columns=key_columns,
                    has_missing_values=stats['summary']['total_missing'] > 0,
                    missing_percentage=int(stats['summary']['missing_percentage']),
                    duplicate_rows=stats['summary']['duplicate_rows']
                )
                
                db.add(sheet)
            
            # Mark as ready
            document.status = 'ready'
            document.processed_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Successfully processed document {document.id}")
            
        except Exception as e:
            logger.error(f"Error in _process_document: {str(e)}")
            raise
    
    async def get_document(
        self,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[ExcelDocument]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            user_id: User ID (for authorization)
            db: Database session
            
        Returns:
            ExcelDocument or None if not found
        """
        result = await db.execute(
            select(ExcelDocument)
            .where(
                ExcelDocument.id == document_id,
                ExcelDocument.user_id == user_id
            )
        )
        document = result.scalar_one_or_none()
        
        if document:
            document.last_accessed_at = datetime.utcnow()
            await db.commit()
        
        return document
    
    async def get_user_documents(
        self,
        user_id: int,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50
    ) -> List[ExcelDocument]:
        """
        Get all documents for a user.
        
        Args:
            user_id: User ID
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ExcelDocuments
        """
        result = await db.execute(
            select(ExcelDocument)
            .where(ExcelDocument.user_id == user_id)
            .order_by(ExcelDocument.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_document_sheets(
        self,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> List[ExcelSheet]:
        """
        Get all sheets for a document.
        
        Args:
            document_id: Document ID
            user_id: User ID (for authorization)
            db: Database session
            
        Returns:
            List of ExcelSheets
        """
        # Verify document ownership
        document = await self.get_document(document_id, user_id, db)
        if not document:
            return []
        
        result = await db.execute(
            select(ExcelSheet)
            .where(ExcelSheet.document_id == document_id)
            .order_by(ExcelSheet.sheet_index)
        )
        return list(result.scalars().all())
    
    async def get_sheet_preview(
        self,
        document_id: int,
        sheet_name: str,
        user_id: int,
        db: AsyncSession,
        rows: int = 10
    ) -> Dict[str, Any]:
        """
        Get a preview of sheet data.
        
        Args:
            document_id: Document ID
            sheet_name: Sheet name
            user_id: User ID (for authorization)
            db: Database session
            rows: Number of rows to preview
            
        Returns:
            Preview data dictionary
        """
        # Verify document ownership
        document = await self.get_document(document_id, user_id, db)
        if not document:
            raise ValueError("Document not found")
        
        # Get preview
        preview = await self.processor.get_sheet_preview(
            document.file_path,
            sheet_name,
            rows
        )
        
        return preview
    
    async def delete_document(
        self,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> bool:
        """
        Delete a document and its associated data.
        
        Args:
            document_id: Document ID
            user_id: User ID (for authorization)
            db: Database session
            
        Returns:
            True if deleted, False if not found
        """
        # Verify document ownership
        document = await self.get_document(document_id, user_id, db)
        if not document:
            return False
        
        # Delete file
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database (cascades to sheets, queries, visualizations)
        await db.delete(document)
        await db.commit()
        
        logger.info(f"Deleted document {document_id}")
        return True
    
    async def save_query(
        self,
        document_id: int,
        user_id: int,
        query_text: str,
        target_sheet: Optional[str],
        db: AsyncSession
    ) -> ExcelQuery:
        """
        Save a natural language query.
        
        Args:
            document_id: Document ID
            user_id: User ID
            query_text: Natural language query
            target_sheet: Target sheet name (optional)
            db: Database session
            
        Returns:
            Created ExcelQuery instance
        """
        query = ExcelQuery(
            document_id=document_id,
            user_id=user_id,
            query_text=query_text,
            target_sheet=target_sheet,
            status='pending'
        )
        
        db.add(query)
        await db.commit()
        await db.refresh(query)
        
        return query
    
    async def execute_query(
        self,
        query_id: int,
        user_id: int,
        db: AsyncSession
    ) -> ExcelQuery:
        """
        Execute a saved natural language query.
        
        Args:
            query_id: Query ID to execute
            user_id: User ID (for authorization)
            db: Database session
            
        Returns:
            Updated ExcelQuery with results
            
        Raises:
            ValueError: If query processor not initialized or query not found
        """
        if not self.query_processor:
            raise ValueError("Query processor not initialized - Anthropic API key required")
        
        # Get query
        result = await db.execute(
            select(ExcelQuery)
            .where(
                ExcelQuery.id == query_id,
                ExcelQuery.user_id == user_id
            )
        )
        query = result.scalar_one_or_none()
        
        if not query:
            raise ValueError(f"Query {query_id} not found")
        
        # Get document and sheet
        document = await self.get_document(query.document_id, user_id, db)
        
        if not document:
            query.status = 'error'
            query.error_message = f"Document {query.document_id} not found"
            await db.commit()
            return query
        
        # Find target sheet
        sheet_result = await db.execute(
            select(ExcelSheet)
            .where(
                ExcelSheet.document_id == query.document_id
            )
        )
        sheets = list(sheet_result.scalars().all())
        sheet = next((s for s in sheets if s.sheet_name == query.target_sheet), None)
        
        if not sheet:
            query.status = 'error'
            query.error_message = f"Sheet '{query.target_sheet}' not found"
            await db.commit()
            return query
        
        try:
            # Update status
            query.status = 'processing'
            await db.commit()
            
            # Generate cache key
            cache_key = self.query_optimizer.get_cache_key(
                query_text=query.query_text,
                document_id=document.id,
                sheet_name=sheet.sheet_name
            )
            
            # Check cache first
            cached_result = self.query_optimizer.get_cached_result(cache_key)
            
            if cached_result:
                # Use cached result
                logger.info(f"Using cached result for query {query_id}")
                query.status = 'success'
                query.generated_code = cached_result.get("code")
                query.code_explanation = cached_result.get("explanation")
                query.result = cached_result.get("result")
                query.execution_time_ms = cached_result.get("execution_time_ms", 0)
                
                await db.commit()
                await db.refresh(query)
                return query
            
            # Generate code using query processor
            query_result = await self.query_processor.process_query(
                user_question=query.query_text,
                document=document,
                sheet=sheet,
                db=None  # Pass None since async not supported in query processor yet
            )
            
            # Save generated code
            query.generated_code = query_result["code"]
            query.code_explanation = query_result["explanation"]
            
            # Load dataframe for execution
            import pandas as pd
            df = pd.read_excel(document.file_path, sheet_name=sheet.sheet_name)
            
            # Execute code
            execution_result = self.code_executor.execute(
                code=query_result["code"],
                dataframe=df,
                validate=True
            )
            
            if execution_result["success"]:
                query.status = 'success'
                query.result = execution_result["result"]
                query.execution_time_ms = execution_result["execution_time_ms"]
                
                # Cache successful result
                cache_data = {
                    "code": query.generated_code,
                    "explanation": query.code_explanation,
                    "result": query.result,
                    "execution_time_ms": query.execution_time_ms,
                    "document_id": document.id,
                    "query_text": query.query_text
                }
                self.query_optimizer.cache_result(cache_key, cache_data)
                
                # Record metrics
                self.query_optimizer.record_query_execution(
                    query_text=query.query_text,
                    execution_time_ms=query.execution_time_ms or 0,
                    success=True
                )
            else:
                query.status = 'error'
                query.error_message = execution_result["error"]
                query.execution_time_ms = execution_result["execution_time_ms"]
                
                # Record failed execution
                self.query_optimizer.record_query_execution(
                    query_text=query.query_text,
                    execution_time_ms=query.execution_time_ms or 0,
                    success=False
                )
            
            await db.commit()
            await db.refresh(query)
            
            logger.info(f"Query {query_id} executed successfully")
            return query
            
        except Exception as e:
            logger.error(f"Error executing query {query_id}: {str(e)}")
            query.status = 'error'
            query.error_message = str(e)
            await db.commit()
            return query
    
    async def get_query_history(
        self,
        document_id: int,
        user_id: int,
        db: AsyncSession,
        limit: int = 20
    ) -> List[ExcelQuery]:
        """
        Get query history for a document.
        
        Args:
            document_id: Document ID
            user_id: User ID (for authorization)
            db: Database session
            limit: Maximum number of queries to return
            
        Returns:
            List of ExcelQueries
        """
        result = await db.execute(
            select(ExcelQuery)
            .where(
                ExcelQuery.document_id == document_id,
                ExcelQuery.user_id == user_id
            )
            .order_by(ExcelQuery.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.sheet_manager.get_cache_stats()
    
    def clear_cache(self) -> None:
        """Clear the sheet cache."""
        self.sheet_manager.clear_cache()
    
    def get_optimizer_metrics(self) -> Dict[str, Any]:
        """Get query optimizer performance metrics."""
        return self.query_optimizer.get_metrics()
    
    def get_optimizer_cache_stats(self) -> Dict[str, Any]:
        """Get query optimizer cache statistics."""
        return self.query_optimizer.get_cache_statistics()
    
    def clear_query_cache(self) -> int:
        """Clear query result cache."""
        return self.query_optimizer.clear_cache()
    
    def invalidate_document_queries(self, document_id: int) -> int:
        """Invalidate all cached queries for a document."""
        return self.query_optimizer.invalidate_document_cache(document_id)
    
    async def generate_example_questions(
        self,
        document_id: int,
        sheet_name: Optional[str],
        user_id: int,
        db: AsyncSession
    ) -> List[str]:
        """
        Generate intelligent example questions based on document columns.
        
        Args:
            document_id: Document ID
            sheet_name: Optional sheet name (uses first sheet if None)
            user_id: User ID
            db: Database session
            
        Returns:
            List of example questions
        """
        # Get document
        document = await self.get_document(document_id, user_id, db)
        if not document:
            raise ValueError("Document not found")
        
        # Get sheet metadata
        if not sheet_name:
            # Use first sheet
            sheets = await self.get_document_sheets(document_id, user_id, db)
            if not sheets:
                raise ValueError("No sheets found in document")
            sheet_name = sheets[0].sheet_name
        
        # Get sheet info and load dataframe to get column types
        sheet_info = self.sheet_manager.get_sheet_info(document.file_path, sheet_name)
        columns = sheet_info.get("columns", [])
        
        # Load sheet to get column types
        df = self.sheet_manager.load_sheet(document.file_path, sheet_name)
        column_types = {col: str(df[col].dtype) for col in df.columns}
        
        # Generate smart questions based on column names and types
        questions = self._generate_smart_questions(columns, column_types)
        
        return questions
    
    def _generate_smart_questions(self, columns: List[str], column_types: Dict[str, str]) -> List[str]:
        """
        Generate smart example questions based on available columns.
        
        Args:
            columns: List of column names
            column_types: Dict mapping column names to data types
            
        Returns:
            List of example questions
        """
        questions = []
        
        # Find numeric columns for aggregation questions
        numeric_cols = [col for col in columns if column_types.get(col) in ['int64', 'float64', 'numeric']]
        
        # Find categorical columns for grouping questions
        categorical_cols = [col for col in columns if column_types.get(col) in ['object', 'string', 'category']]
        
        # Find date columns
        date_cols = [col for col in columns if 'date' in column_types.get(col, '').lower() or 'date' in col.lower()]
        
        # Question 1: List columns (always useful)
        questions.append("What columns are available?")
        
        # Question 2: Aggregation by category (if we have both numeric and categorical)
        if numeric_cols and categorical_cols:
            num_col = numeric_cols[0]
            cat_col = categorical_cols[0]
            questions.append(f"What is the total {num_col} by {cat_col}?")
        
        # Question 3: Average of numeric column
        if numeric_cols:
            num_col = numeric_cols[0] if len(numeric_cols) > 0 else numeric_cols[0]
            questions.append(f"What is the average {num_col}?")
        
        # Question 4: Top N records (if we have numeric for sorting)
        if numeric_cols and len(columns) >= 2:
            sort_col = numeric_cols[0]
            display_col = categorical_cols[0] if categorical_cols else columns[0]
            questions.append(f"Show me the top 10 {display_col} by {sort_col}")
        
        # Question 5: Count unique values (if we have categorical)
        if categorical_cols:
            cat_col = categorical_cols[0]
            questions.append(f"How many unique {cat_col} are there?")
        
        # Limit to 4-5 questions
        return questions[:5]
    
    def _get_mime_type(self, file_ext: str) -> str:
        """Get MIME type from file extension."""
        mime_types = {
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.xlsm': 'application/vnd.ms-excel.sheet.macroEnabled.12'
        }
        return mime_types.get(file_ext.lower(), 'application/octet-stream')
