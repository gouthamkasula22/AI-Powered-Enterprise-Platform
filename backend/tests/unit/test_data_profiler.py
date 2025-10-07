"""
Unit Tests for Data Profiler

Tests for statistical analysis and data profiling.
"""

import pytest
import pandas as pd
import numpy as np
from backend.src.infrastructure.excel import DataProfiler


class TestDataProfiler:
    """Test suite for DataProfiler."""
    
    @pytest.fixture
    def profiler(self):
        """Create DataProfiler instance."""
        return DataProfiler()
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 30, 40],
            'salary': [50000, 60000, 70000, 60000, 80000],
            'active': [True, False, True, True, False],
            'hire_date': pd.date_range('2020-01-01', periods=5),
            'percentage': [0.1, 0.2, 0.3, 0.4, 0.5]
        })
    
    def test_generate_statistics(self, profiler, sample_dataframe):
        """Test comprehensive statistics generation."""
        stats = profiler.generate_statistics(sample_dataframe)
        
        assert stats['row_count'] == 5
        assert stats['column_count'] == 7
        assert 'columns' in stats
        assert 'summary' in stats
        assert stats['summary']['total_cells'] == 35
    
    def test_numeric_stats(self, profiler):
        """Test numeric column statistics."""
        df = pd.DataFrame({'values': [1, 2, 3, 4, 5]})
        stats = profiler.generate_statistics(df)
        
        col_stats = stats['columns']['values']
        assert col_stats['data_type'] == 'numeric'
        assert col_stats['min'] == 1.0
        assert col_stats['max'] == 5.0
        assert col_stats['mean'] == 3.0
        assert col_stats['median'] == 3.0
    
    def test_text_stats(self, profiler):
        """Test text column statistics."""
        df = pd.DataFrame({'names': ['Alice', 'Bob', 'Charlie']})
        stats = profiler.generate_statistics(df)
        
        col_stats = stats['columns']['names']
        assert col_stats['data_type'] == 'text'
        assert col_stats['min_length'] == 3
        assert col_stats['max_length'] == 7
        assert col_stats['unique_count'] == 3
    
    def test_boolean_stats(self, profiler):
        """Test boolean column statistics."""
        df = pd.DataFrame({'flags': [True, False, True, True]})
        stats = profiler.generate_statistics(df)
        
        col_stats = stats['columns']['flags']
        assert col_stats['data_type'] == 'boolean'
        assert col_stats['true_count'] == 3
        assert col_stats['false_count'] == 1
        assert col_stats['true_percentage'] == 75.0
    
    def test_datetime_stats(self, profiler):
        """Test datetime column statistics."""
        df = pd.DataFrame({
            'dates': pd.date_range('2020-01-01', periods=5)
        })
        stats = profiler.generate_statistics(df)
        
        col_stats = stats['columns']['dates']
        assert col_stats['data_type'] == 'datetime'
        assert col_stats['range_days'] == 4
    
    def test_detect_data_types(self, profiler, sample_dataframe):
        """Test semantic type detection."""
        semantic_types = profiler.detect_data_types(sample_dataframe)
        
        assert semantic_types['id'] == 'identifier'
        assert semantic_types['name'] == 'text'
        assert semantic_types['age'] == 'numeric'
        assert semantic_types['active'] == 'boolean'
    
    def test_identify_key_columns(self, profiler, sample_dataframe):
        """Test key column identification."""
        key_columns = profiler.identify_key_columns(sample_dataframe)
        
        assert 'id' in key_columns
    
    def test_missing_values(self, profiler):
        """Test handling of missing values."""
        df = pd.DataFrame({
            'values': [1, 2, None, 4, 5]
        })
        stats = profiler.generate_statistics(df)
        
        assert stats['summary']['total_missing'] == 1
        assert stats['columns']['values']['null_count'] == 1
        assert stats['columns']['values']['null_percentage'] == 20.0
    
    def test_duplicates(self, profiler):
        """Test duplicate detection."""
        df = pd.DataFrame({
            'col1': [1, 1, 2, 3, 3],
            'col2': ['a', 'a', 'b', 'c', 'c']
        })
        stats = profiler.generate_statistics(df)
        
        assert stats['summary']['duplicate_rows'] == 2
    
    def test_empty_dataframe(self, profiler):
        """Test handling empty DataFrame."""
        df = pd.DataFrame()
        stats = profiler.generate_statistics(df)
        
        assert stats['row_count'] == 0
        assert stats['column_count'] == 0
    
    def test_percentage_detection(self, profiler):
        """Test percentage type detection."""
        df = pd.DataFrame({'percent': [0.1, 0.2, 0.3, 0.4, 0.5]})
        semantic_types = profiler.detect_data_types(df)
        
        assert semantic_types['percent'] == 'percentage'
    
    def test_categorical_detection(self, profiler):
        """Test categorical type detection."""
        df = pd.DataFrame({
            'category': ['A', 'B', 'A', 'B', 'A'] * 20  # 100 rows with 2 unique values
        })
        semantic_types = profiler.detect_data_types(df)
        
        assert semantic_types['category'] == 'categorical'
