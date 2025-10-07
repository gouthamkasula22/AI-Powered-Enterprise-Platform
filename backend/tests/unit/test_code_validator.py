"""
Unit tests for Code Validator
"""

import pytest
from src.infrastructure.excel.code_validator import CodeValidator


class TestCodeValidator:
    """Tests for CodeValidator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.validator = CodeValidator()
    
    def test_valid_code(self):
        """Test that valid pandas code passes validation."""
        code = """
result = df['Sales'].mean()
"""
        is_valid, error = self.validator.validate(code)
        assert is_valid is True
        assert error is None
    
    def test_empty_code(self):
        """Test that empty code fails validation."""
        is_valid, error = self.validator.validate("")
        assert is_valid is False
        assert error is not None and "empty" in error.lower()
    
    def test_no_result_variable(self):
        """Test that code without result variable fails."""
        code = """
x = df['Sales'].mean()
"""
        is_valid, error = self.validator.validate(code)
        assert is_valid is False
        assert error is not None and "result" in error.lower()
    
    def test_forbidden_import(self):
        """Test that import statements are blocked."""
        code = """
import os
result = df['Sales'].mean()
"""
        is_valid, error = self.validator.validate(code)
        assert is_valid is False
        assert error is not None and "import" in error.lower()
    
    def test_forbidden_eval(self):
        """Test that eval() is blocked."""
        code = """
result = eval("df['Sales'].mean()")
"""
        is_valid, error = self.validator.validate(code)
        assert is_valid is False
        assert error is not None and "eval" in error.lower()
    
    def test_forbidden_file_io(self):
        """Test that file I/O methods are blocked."""
        code = """
df.to_csv('output.csv')
result = 1
"""
        is_valid, error = self.validator.validate(code)
        assert is_valid is False
        assert "file I/O" in error.lower() or "to_csv" in error.lower()
    
    def test_syntax_error(self):
        """Test that syntax errors are caught."""
        code = """
result = df['Sales'.mean()
"""
        is_valid, error = self.validator.validate(code)
        assert is_valid is False
        assert error is not None and "syntax" in error.lower()
    
    def test_max_lines_exceeded(self):
        """Test that code exceeding max lines fails."""
        validator = CodeValidator(max_lines=5)
        code = "\n".join([f"x{i} = {i}" for i in range(10)])
        code += "\nresult = x0"
        
        is_valid, error = validator.validate(code)
        assert is_valid is False
        assert error is not None and "exceeds" in error.lower()
    
    def test_safety_report(self):
        """Test that safety report is generated correctly."""
        code = """
result = df['Sales'].mean()
"""
        report = self.validator.get_safety_report(code)
        
        assert report["is_safe"] is True
        assert report["has_result"] is True
        assert len(report["issues"]) == 0
    
    def test_safety_report_with_issues(self):
        """Test safety report with code issues."""
        code = """
import os
x = df['Sales'].mean()
"""
        report = self.validator.get_safety_report(code)
        
        assert report["is_safe"] is False
        assert report["has_result"] is False
        assert len(report["issues"]) > 0
