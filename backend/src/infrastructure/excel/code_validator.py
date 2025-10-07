"""
Code Validator for ensuring safe pandas code execution.
"""

import ast
import logging
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)


class CodeValidator:
    """
    Validates generated pandas code for safety before execution.
    """
    
    # Allowed built-in functions
    ALLOWED_BUILTINS = {
        'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'float', 'int',
        'len', 'list', 'max', 'min', 'range', 'round', 'set', 'sorted',
        'str', 'sum', 'tuple', 'zip', 'isinstance', 'type'
    }
    
    # Dangerous AST node types that should not be allowed
    FORBIDDEN_NODES = {
        ast.Import: "Imports are not allowed",
        ast.ImportFrom: "Imports are not allowed",
        ast.FunctionDef: "Function definitions are not allowed",
        ast.AsyncFunctionDef: "Async function definitions are not allowed",
        ast.ClassDef: "Class definitions are not allowed",
        ast.Delete: "Delete operations are not allowed",
        ast.Global: "Global declarations are not allowed",
        ast.Nonlocal: "Nonlocal declarations are not allowed",
        ast.With: "With statements are not allowed (potential file I/O)",
        ast.AsyncWith: "Async with statements are not allowed",
        ast.Raise: "Raise statements are not allowed",
        ast.Try: "Try-except blocks are not allowed",
    }
    
    # Dangerous function/attribute names
    FORBIDDEN_NAMES = {
        'eval', 'exec', 'compile', 'open', '__import__',
        'input', 'raw_input', 'file', 'exit', 'quit',
        'reload', 'help', 'vars', 'locals', 'globals',
        'dir', 'getattr', 'setattr', 'delattr', 'hasattr',
        '__builtins__', '__dict__', '__class__', '__bases__',
        '__subclasses__', '__code__', '__closure__'
    }
    
    # Dangerous pandas/dataframe methods
    FORBIDDEN_DF_METHODS = {
        'to_pickle', 'to_sql', 'to_hdf', 'to_feather', 'to_parquet',
        'to_excel', 'to_csv', 'to_json', 'to_html', 'to_latex',
        'read_pickle', 'read_sql', 'read_hdf', 'read_feather',
        'read_parquet', 'read_excel', 'read_csv', 'read_json'
    }
    
    def __init__(self, max_lines: int = 50):
        """
        Initialize code validator.
        
        Args:
            max_lines: Maximum number of lines allowed in code
        """
        self.max_lines = max_lines
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate code for safety.
        
        Args:
            code: Python code to validate
        
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if code is safe, False otherwise
            - error_message: None if valid, error description if invalid
        """
        try:
            # Check if code is empty
            if not code or not code.strip():
                return False, "Code cannot be empty"
            
            # Check code length
            lines = code.split('\n')
            if len(lines) > self.max_lines:
                return False, f"Code exceeds maximum {self.max_lines} lines"
            
            # Parse code into AST
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                return False, f"Syntax error: {str(e)}"
            
            # Check for forbidden nodes
            is_valid, error = self._check_forbidden_nodes(tree)
            if not is_valid:
                return False, error
            
            # Check for forbidden names
            is_valid, error = self._check_forbidden_names(tree)
            if not is_valid:
                return False, error
            
            # Check for dangerous method calls
            is_valid, error = self._check_dangerous_methods(tree)
            if not is_valid:
                return False, error
            
            # Ensure 'result' variable is assigned
            if not self._has_result_assignment(tree):
                return False, "Code must assign a value to 'result' variable"
            
            logger.info("Code validation passed")
            return True, None
            
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def _check_forbidden_nodes(self, tree: ast.AST) -> Tuple[bool, Optional[str]]:
        """Check for forbidden AST node types."""
        for node in ast.walk(tree):
            for forbidden_type, message in self.FORBIDDEN_NODES.items():
                if isinstance(node, forbidden_type):
                    logger.warning(f"Forbidden node type found: {forbidden_type.__name__}")
                    return False, message
        return True, None
    
    def _check_forbidden_names(self, tree: ast.AST) -> Tuple[bool, Optional[str]]:
        """Check for forbidden function/variable names."""
        for node in ast.walk(tree):
            # Check Name nodes (variables and functions)
            if isinstance(node, ast.Name):
                if node.id in self.FORBIDDEN_NAMES:
                    logger.warning(f"Forbidden name found: {node.id}")
                    return False, f"Use of '{node.id}' is not allowed"
            
            # Check Call nodes (function calls)
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in self.FORBIDDEN_NAMES:
                    logger.warning(f"Forbidden function call: {func_name}")
                    return False, f"Call to '{func_name}' is not allowed"
        
        return True, None
    
    def _check_dangerous_methods(self, tree: ast.AST) -> Tuple[bool, Optional[str]]:
        """Check for dangerous pandas/dataframe methods."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's a method call (Attribute)
                if isinstance(node.func, ast.Attribute):
                    method_name = node.func.attr
                    if method_name in self.FORBIDDEN_DF_METHODS:
                        logger.warning(f"Forbidden method call: {method_name}")
                        return False, f"Method '{method_name}' is not allowed (file I/O)"
        
        return True, None
    
    def _has_result_assignment(self, tree: ast.AST) -> bool:
        """Check if code assigns to 'result' variable."""
        for node in ast.walk(tree):
            # Check for assignment to 'result'
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'result':
                        return True
            
            # Check for augmented assignment (result += x)
            if isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name) and node.target.id == 'result':
                    return True
        
        return False
    
    def _get_function_name(self, func_node: ast.AST) -> Optional[str]:
        """Extract function name from various AST node types."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return func_node.attr
        elif isinstance(func_node, ast.Call):
            return self._get_function_name(func_node.func)
        return None
    
    def get_safety_report(self, code: str) -> dict:
        """
        Generate a detailed safety report for the code.
        
        Args:
            code: Python code to analyze
        
        Returns:
            Dictionary with safety analysis results
        """
        report = {
            "is_safe": False,
            "issues": [],
            "warnings": [],
            "line_count": 0,
            "has_result": False
        }
        
        try:
            # Basic checks
            if not code or not code.strip():
                report["issues"].append("Code is empty")
                return report
            
            lines = [l for l in code.split('\n') if l.strip()]
            report["line_count"] = len(lines)
            
            if len(lines) > self.max_lines:
                report["issues"].append(f"Code exceeds {self.max_lines} lines")
            
            # Parse AST
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                report["issues"].append(f"Syntax error: {str(e)}")
                return report
            
            # Check for issues
            is_valid, error = self._check_forbidden_nodes(tree)
            if not is_valid:
                report["issues"].append(error)
            
            is_valid, error = self._check_forbidden_names(tree)
            if not is_valid:
                report["issues"].append(error)
            
            is_valid, error = self._check_dangerous_methods(tree)
            if not is_valid:
                report["issues"].append(error)
            
            # Check result assignment
            report["has_result"] = self._has_result_assignment(tree)
            if not report["has_result"]:
                report["issues"].append("No assignment to 'result' variable")
            
            # Check for warnings (not blocking, but noteworthy)
            for node in ast.walk(tree):
                # Warn about lambda functions
                if isinstance(node, ast.Lambda):
                    report["warnings"].append("Lambda functions detected")
                
                # Warn about list comprehensions (can be memory intensive)
                if isinstance(node, ast.ListComp):
                    report["warnings"].append("List comprehension detected")
            
            # Overall safety determination
            report["is_safe"] = len(report["issues"]) == 0
            
        except Exception as e:
            report["issues"].append(f"Analysis error: {str(e)}")
        
        return report
