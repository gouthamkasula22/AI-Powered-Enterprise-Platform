"""
Query Processor for converting natural language to pandas code using Claude API.
"""

import json
import logging
from typing import Dict, Optional, Any
from anthropic import Anthropic
from anthropic.types import TextBlock
from sqlalchemy.orm import Session

from src.domain.models.excel_models import ExcelDocument, ExcelSheet
from src.infrastructure.excel.sheet_manager import SheetManager
from .prompts import (
    SYSTEM_PROMPT,
    FEW_SHOT_EXAMPLES,
    build_query_prompt,
    build_refinement_prompt
)

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Processes natural language queries and generates pandas code using Claude API.
    """
    
    def __init__(
        self,
        anthropic_api_key: str,
        sheet_manager: SheetManager,
        model: str = "claude-3-haiku-20240307",
        max_tokens: int = 2000,
        temperature: float = 0.0
    ):
        """
        Initialize query processor.
        
        Args:
            anthropic_api_key: Anthropic API key
            sheet_manager: Sheet manager for data access
            model: Claude model to use (default: claude-3-haiku-20240307)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0 = deterministic)
        """
        self.client = Anthropic(api_key=anthropic_api_key)
        self.sheet_manager = sheet_manager
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    async def process_query(
        self,
        user_question: str,
        document: ExcelDocument,
        sheet: ExcelSheet,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language query and generate pandas code.
        
        Args:
            user_question: User's natural language question
            document: Excel document
            sheet: Excel sheet to query
            db: Database session
        
        Returns:
            Dictionary containing:
                - code: Generated pandas code
                - explanation: Code explanation
                - result_type: Expected result type
                - context_used: Context information used
        
        Raises:
            Exception: If query processing fails
        """
        try:
            logger.info(f"Processing query for document {document.id}, sheet {sheet.sheet_name}")
            
            # Get sheet metadata
            sheet_metadata = self._extract_sheet_metadata(sheet)
            
            # Get sample data
            preview_data = self.sheet_manager.get_sheet_preview(
                document.file_path,
                sheet.sheet_name,
                page=1,
                page_size=5
            )
            
            # Build prompt
            context_prompt = build_query_prompt(
                user_question=user_question,
                sheet_name=sheet.sheet_name,
                sheet_metadata=sheet_metadata,
                preview_data=preview_data["data"]
            )
            
            # Call Claude API
            response = await self._call_claude_api(context_prompt)
            
            # Parse response
            result = self._parse_response(response)
            
            # Add context information
            columns = sheet_metadata.get("columns", [])
            # Handle both list of strings and list of dicts
            if columns and isinstance(columns[0], dict):
                column_names = [col["name"] for col in columns]
            else:
                column_names = columns if isinstance(columns, list) else []
            
            result["context_used"] = {
                "sheet_name": sheet.sheet_name,
                "row_count": sheet_metadata["row_count"],
                "column_count": sheet_metadata["column_count"],
                "columns": column_names
            }
            
            logger.info(f"Successfully generated code for query: {user_question[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to process query: {str(e)}")
    
    async def refine_query(
        self,
        original_question: str,
        original_code: str,
        error_message: Optional[str],
        refinement_request: str,
        document: ExcelDocument,
        sheet: ExcelSheet
    ) -> Dict[str, Any]:
        """
        Refine a previous query based on error or user feedback.
        
        Args:
            original_question: Original question
            original_code: Original generated code
            error_message: Error message if code failed
            refinement_request: User's refinement request
            document: Excel document
            sheet: Excel sheet
        
        Returns:
            Dictionary with refined code and explanation
        """
        try:
            logger.info(f"Refining query: {refinement_request[:50]}...")
            
            # Get sheet context again
            sheet_metadata = self._extract_sheet_metadata(sheet)
            preview_data = self.sheet_manager.get_sheet_preview(
                document.file_path,
                sheet.sheet_name,
                page=1,
                page_size=5
            )
            
            # Build refinement prompt
            refinement_prompt = build_refinement_prompt(
                original_question=original_question,
                original_code=original_code,
                error_message=error_message or "",
                refinement_request=refinement_request
            )
            
            # Add data context
            context_prompt = build_query_prompt(
                user_question=refinement_request,
                sheet_name=sheet.sheet_name,
                sheet_metadata=sheet_metadata,
                preview_data=preview_data["data"]
            )
            
            full_prompt = refinement_prompt + "\n\n" + context_prompt
            
            # Call Claude API
            response = await self._call_claude_api(full_prompt)
            
            # Parse response
            result = self._parse_response(response)
            result["is_refinement"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error refining query: {str(e)}")
            raise Exception(f"Failed to refine query: {str(e)}")
    
    async def _call_claude_api(self, user_prompt: str) -> str:
        """
        Call Claude API with the given prompt.
        
        Args:
            user_prompt: User prompt to send
        
        Returns:
            API response text
        """
        try:
            # Combine system prompt with few-shot examples
            full_system_prompt = f"{SYSTEM_PROMPT}\n\n{FEW_SHOT_EXAMPLES}"
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=full_system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )
            
            # Extract text from response - only process TextBlock types
            response_text = ""
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text
            
            if not response_text:
                raise Exception("No text content in API response")
            
            logger.debug(f"Claude API response: {response_text[:200]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            raise Exception(f"API call failed: {str(e)}")
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Claude API response into structured format.
        
        Args:
            response_text: Raw response from Claude
        
        Returns:
            Parsed response dictionary
        """
        try:
            # Try to extract JSON from response
            # Claude might wrap JSON in markdown code blocks
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            parsed = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["code", "explanation", "result_type"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}")
            # Try to extract code from plain text response
            if "result =" in response_text:
                return {
                    "code": response_text,
                    "explanation": "Code extracted from plain text response",
                    "result_type": "unknown"
                }
            raise Exception(f"Failed to parse response: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            raise Exception(f"Failed to parse response: {str(e)}")
    
    def _extract_sheet_metadata(self, sheet: ExcelSheet) -> Dict[str, Any]:
        """
        Extract metadata from sheet for context building.
        
        Args:
            sheet: Excel sheet entity
        
        Returns:
            Sheet metadata dictionary
        """
        try:
            metadata = {
                "row_count": sheet.row_count,
                "column_count": sheet.column_count,
                "columns": sheet.columns or [],
                "column_types": sheet.column_types or {},
                "total_missing": sheet.missing_percentage or 0,
                "duplicate_rows": sheet.duplicate_rows or 0
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting sheet metadata: {str(e)}")
            return {
                "row_count": 0,
                "column_count": 0,
                "columns": [],
                "column_types": {},
                "total_missing": 0,
                "duplicate_rows": 0
            }
    
    def get_suggested_queries(self, sheet: ExcelSheet) -> list[str]:
        """
        Generate suggested queries based on sheet structure.
        
        Args:
            sheet: Excel sheet
        
        Returns:
            List of suggested query strings
        """
        suggestions = []
        
        try:
            columns = sheet.columns or []
            
            # Columns are stored as a list of strings
            if isinstance(columns, list) and columns:
                # Use first few columns for generic suggestions
                col1 = columns[0] if len(columns) > 0 else None
                col2 = columns[1] if len(columns) > 1 else None
                
                if col1:
                    suggestions.append(f"What is the average {col1}?")
                    suggestions.append(f"What is the total {col1}?")
                
                if col1 and col2:
                    suggestions.append(f"Group by {col2} and sum {col1}")
                    suggestions.append(f"Show top 10 rows sorted by {col1}")
            
            # Generic suggestions
            suggestions.append(f"How many rows are in this data?")
            suggestions.append(f"Show me the first 10 rows")
            
        except Exception as e:
            logger.warning(f"Error generating suggestions: {str(e)}")
        
        return suggestions[:5]  # Return max 5 suggestions
