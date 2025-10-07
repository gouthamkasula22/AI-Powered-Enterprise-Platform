"""
Code Executor for safe pandas code execution in sandboxed environment.
"""

import sys
import io
import logging
import traceback
from typing import Dict, Any, Optional
from contextlib import redirect_stdout, redirect_stderr
import pandas as pd
import numpy as np
from datetime import datetime

from .code_validator import CodeValidator

logger = logging.getLogger(__name__)


class CodeExecutor:
    """
    Executes validated pandas code in a restricted environment.
    """
    
    def __init__(
        self,
        timeout_seconds: int = 30,
        max_result_size: int = 10000
    ):
        """
        Initialize code executor.
        
        Args:
            timeout_seconds: Maximum execution time
            max_result_size: Maximum number of rows in result
        """
        self.timeout_seconds = timeout_seconds
        self.max_result_size = max_result_size
        self.validator = CodeValidator()
    
    def execute(
        self,
        code: str,
        dataframe: pd.DataFrame,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Execute pandas code with the given dataframe.
        
        Args:
            code: Python code to execute
            dataframe: DataFrame to operate on
            validate: Whether to validate code before execution
        
        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - result: Execution result (if successful)
                - error: Error message (if failed)
                - execution_time_ms: Execution time in milliseconds
                - stdout: Captured stdout
                - stderr: Captured stderr
        """
        start_time = datetime.now()
        
        try:
            # Validate code if requested
            if validate:
                is_valid, error_msg = self.validator.validate(code)
                if not is_valid:
                    logger.warning(f"Code validation failed: {error_msg}")
                    return {
                        "success": False,
                        "result": None,
                        "error": f"Validation error: {error_msg}",
                        "execution_time_ms": 0,
                        "stdout": "",
                        "stderr": ""
                    }
            
            # Prepare safe execution environment
            safe_namespace = self._create_safe_namespace(dataframe)
            
            # Capture stdout and stderr
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Execute code
                exec(code, safe_namespace)
            
            # Get result from namespace
            result = safe_namespace.get('result', None)
            
            if result is None:
                return {
                    "success": False,
                    "result": None,
                    "error": "Code did not produce a 'result' variable",
                    "execution_time_ms": self._get_execution_time(start_time),
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": stderr_buffer.getvalue()
                }
            
            # Format result for JSON serialization
            formatted_result = self._format_result(result)
            
            logger.info(f"Code executed successfully in {self._get_execution_time(start_time)}ms")
            
            return {
                "success": True,
                "result": formatted_result,
                "error": None,
                "execution_time_ms": self._get_execution_time(start_time),
                "stdout": stdout_buffer.getvalue(),
                "stderr": stderr_buffer.getvalue()
            }
            
        except Exception as e:
            logger.error(f"Code execution failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "execution_time_ms": self._get_execution_time(start_time),
                "stdout": "",
                "stderr": traceback.format_exc()
            }
    
    def _create_safe_namespace(self, dataframe: pd.DataFrame) -> dict:
        """
        Create restricted namespace for code execution.
        
        Args:
            dataframe: DataFrame to include in namespace
        
        Returns:
            Safe namespace dictionary
        """
        # Only include safe builtins
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'float': float,
            'int': int,
            'len': len,
            'list': list,
            'max': max,
            'min': min,
            'range': range,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'zip': zip,
            'isinstance': isinstance,
            'type': type,
            'print': print,  # Allow print for debugging
        }
        
        # Create namespace with only necessary items
        namespace = {
            '__builtins__': safe_builtins,
            'df': dataframe.copy(),  # Work on a copy
            'pd': pd,
            'np': np,
            'result': None  # Initialize result variable
        }
        
        return namespace
    
    def _format_result(self, result: Any) -> Dict[str, Any]:
        """
        Format execution result for JSON serialization.
        
        Args:
            result: Execution result
        
        Returns:
            Formatted result dictionary
        """
        result_type = type(result).__name__
        
        # Handle different result types
        if isinstance(result, pd.DataFrame):
            return self._format_dataframe(result)
        
        elif isinstance(result, pd.Series):
            return self._format_series(result)
        
        elif isinstance(result, (int, float, bool)):
            return {
                "type": "scalar",
                "value": result,
                "dtype": result_type
            }
        
        elif isinstance(result, str):
            return {
                "type": "string",
                "value": result
            }
        
        elif isinstance(result, (list, tuple)):
            return {
                "type": "array",
                "value": list(result),
                "length": len(result)
            }
        
        elif isinstance(result, dict):
            return {
                "type": "dict",
                "value": result
            }
        
        elif result is None:
            return {
                "type": "null",
                "value": None
            }
        
        else:
            # Try to convert to string
            return {
                "type": "unknown",
                "value": str(result),
                "dtype": result_type
            }
    
    def _format_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Format DataFrame result."""
        # Limit result size
        if len(df) > self.max_result_size:
            logger.warning(f"DataFrame result truncated from {len(df)} to {self.max_result_size} rows")
            df = df.head(self.max_result_size)
        
        # Convert to dict for JSON serialization
        return {
            "type": "dataframe",
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient='records'),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "truncated": len(df) >= self.max_result_size
        }
    
    def _format_series(self, series: pd.Series) -> Dict[str, Any]:
        """Format Series result."""
        # Limit result size
        if len(series) > self.max_result_size:
            logger.warning(f"Series result truncated from {len(series)} to {self.max_result_size} items")
            series = series.head(self.max_result_size)
        
        return {
            "type": "series",
            "name": series.name,
            "length": len(series),
            "data": series.tolist(),
            "dtype": str(series.dtype),
            "truncated": len(series) >= self.max_result_size
        }
    
    def _get_execution_time(self, start_time: datetime) -> int:
        """Calculate execution time in milliseconds."""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000
        return int(duration)
    
    def test_code(self, code: str) -> Dict[str, Any]:
        """
        Test code with a sample DataFrame without full execution.
        
        Args:
            code: Code to test
        
        Returns:
            Test results including validation and syntax check
        """
        result = {
            "valid": False,
            "issues": [],
            "warnings": []
        }
        
        # Validate code
        is_valid, error_msg = self.validator.validate(code)
        if not is_valid:
            result["issues"].append(error_msg)
        else:
            result["valid"] = True
        
        # Get detailed safety report
        safety_report = self.validator.get_safety_report(code)
        result["issues"].extend(safety_report.get("issues", []))
        result["warnings"].extend(safety_report.get("warnings", []))
        
        return result
