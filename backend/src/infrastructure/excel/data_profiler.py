"""
Data Profiler

Generates statistical profiles and insights for Excel data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataProfiler:
    """Generates comprehensive data profiles for DataFrames."""
    
    def __init__(self):
        pass
    
    def generate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive statistics for a DataFrame.
        
        Args:
            df: DataFrame to profile
            
        Returns:
            Dictionary containing statistical summaries
        """
        try:
            stats = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
                'columns': {},
                'summary': {}
            }
            
            # Overall summary
            stats['summary'] = {
                'total_cells': len(df) * len(df.columns),
                'total_missing': int(df.isnull().sum().sum()),
                'missing_percentage': float(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100) if len(df) > 0 else 0,
                'duplicate_rows': int(df.duplicated().sum()),
                'duplicate_percentage': float(df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0
            }
            
            # Per-column statistics
            for col in df.columns:
                col_stats = self._profile_column(df[col], col)
                stats['columns'][col] = col_stats
            
            logger.info(f"Generated statistics for {stats['column_count']} columns")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error generating statistics: {str(e)}")
            raise
    
    def _profile_column(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """
        Profile a single column.
        
        Args:
            series: Pandas Series to profile
            column_name: Name of the column
            
        Returns:
            Dictionary with column statistics
        """
        stats = {
            'name': column_name,
            'dtype': str(series.dtype),
            'count': int(series.count()),
            'null_count': int(series.isnull().sum()),
            'null_percentage': float(series.isnull().sum() / len(series) * 100) if len(series) > 0 else 0,
            'unique_count': int(series.nunique()),
            'unique_percentage': float(series.nunique() / len(series) * 100) if len(series) > 0 else 0
        }
        
        # Type-specific statistics
        if pd.api.types.is_numeric_dtype(series):
            stats.update(self._numeric_stats(series))
        elif pd.api.types.is_string_dtype(series) or series.dtype == object:
            stats.update(self._text_stats(series))
        elif pd.api.types.is_datetime64_any_dtype(series):
            stats.update(self._datetime_stats(series))
        elif pd.api.types.is_bool_dtype(series):
            stats.update(self._boolean_stats(series))
        
        return stats
    
    def _numeric_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Generate statistics for numeric columns."""
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {
                'data_type': 'numeric',
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'std': None,
                'q25': None,
                'q75': None
            }
        
        return {
            'data_type': 'numeric',
            'min': float(clean_series.min()),
            'max': float(clean_series.max()),
            'mean': float(clean_series.mean()),
            'median': float(clean_series.median()),
            'std': float(clean_series.std()) if len(clean_series) > 1 else 0.0,
            'q25': float(clean_series.quantile(0.25)),
            'q75': float(clean_series.quantile(0.75)),
            'sum': float(clean_series.sum()),
            'variance': float(clean_series.var()) if len(clean_series) > 1 else 0.0
        }
    
    def _text_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Generate statistics for text columns."""
        clean_series = series.dropna().astype(str)
        
        if len(clean_series) == 0:
            return {
                'data_type': 'text',
                'min_length': 0,
                'max_length': 0,
                'avg_length': 0.0,
                'most_common': []
            }
        
        lengths = clean_series.str.len()
        value_counts = clean_series.value_counts().head(5)
        
        return {
            'data_type': 'text',
            'min_length': int(lengths.min()),
            'max_length': int(lengths.max()),
            'avg_length': float(lengths.mean()),
            'most_common': [
                {'value': str(val), 'count': int(count)} 
                for val, count in value_counts.items()
            ]
        }
    
    def _datetime_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Generate statistics for datetime columns."""
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {
                'data_type': 'datetime',
                'min_date': None,
                'max_date': None,
                'range_days': 0
            }
        
        min_date = clean_series.min()
        max_date = clean_series.max()
        
        return {
            'data_type': 'datetime',
            'min_date': min_date.isoformat() if pd.notnull(min_date) else None,
            'max_date': max_date.isoformat() if pd.notnull(max_date) else None,
            'range_days': int((max_date - min_date).days) if pd.notnull(min_date) and pd.notnull(max_date) else 0
        }
    
    def _boolean_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Generate statistics for boolean columns."""
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {
                'data_type': 'boolean',
                'true_count': 0,
                'false_count': 0,
                'true_percentage': 0.0
            }
        
        true_count = int(clean_series.sum())
        false_count = len(clean_series) - true_count
        
        return {
            'data_type': 'boolean',
            'true_count': true_count,
            'false_count': false_count,
            'true_percentage': float(true_count / len(clean_series) * 100)
        }
    
    def detect_data_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Detect semantic data types (beyond pandas dtypes).
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary mapping column names to semantic types
        """
        semantic_types = {}
        
        for col in df.columns:
            semantic_types[col] = self._detect_semantic_type(df[col])
        
        return semantic_types
    
    def _detect_semantic_type(self, series: pd.Series) -> str:
        """Detect semantic type of a column."""
        # Skip if too many nulls
        if series.isnull().sum() / len(series) > 0.9:
            return 'mostly_null'
        
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return 'empty'
        
        # Check if all values are unique (potential ID column)
        if clean_series.nunique() == len(clean_series):
            return 'identifier'
        
        # Numeric types
        if pd.api.types.is_numeric_dtype(series):
            # Check if it's a year
            if clean_series.between(1900, 2100).all():
                return 'year'
            # Check if it's a percentage (values between 0 and 1 or 0 and 100)
            if (clean_series >= 0).all() and (clean_series <= 1).all():
                return 'percentage'
            if (clean_series >= 0).all() and (clean_series <= 100).all() and clean_series.nunique() < 100:
                return 'percentage'
            return 'numeric'
        
        # Datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'
        
        # Boolean
        if pd.api.types.is_bool_dtype(series):
            return 'boolean'
        
        # Categorical (text with limited unique values)
        if series.dtype == object:
            unique_ratio = series.nunique() / len(series)
            if unique_ratio < 0.05:  # Less than 5% unique
                return 'categorical'
            return 'text'
        
        return 'unknown'
    
    def identify_key_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Identify potential key/ID columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            List of column names that are likely keys
        """
        key_columns = []
        
        for col in df.columns:
            # Check if column name suggests it's a key
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['id', 'key', 'code', 'number']):
                # Verify it has unique or mostly unique values
                if df[col].nunique() / len(df) > 0.95:
                    key_columns.append(col)
                    continue
            
            # Check if values are all unique
            if df[col].nunique() == len(df):
                key_columns.append(col)
        
        return key_columns
