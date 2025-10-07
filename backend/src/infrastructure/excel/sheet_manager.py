"""
Sheet Manager

Manages multi-sheet Excel navigation and data caching.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class SheetCache:
    """Simple in-memory cache for sheet data."""
    
    def __init__(self, ttl_minutes: int = 30, max_size_mb: int = 100):
        """
        Initialize cache.
        
        Args:
            ttl_minutes: Time-to-live for cached entries in minutes
            max_size_mb: Maximum cache size in megabytes
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._current_size_bytes = 0
    
    def _generate_key(self, file_path: str, sheet_name: str) -> str:
        """Generate cache key from file path and sheet name."""
        key_string = f"{file_path}:{sheet_name}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, file_path: str, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Retrieve data from cache.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet
            
        Returns:
            Cached DataFrame or None if not found/expired
        """
        key = self._generate_key(file_path, sheet_name)
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if datetime.now() - entry['timestamp'] > self._ttl:
            self._remove(key)
            return None
        
        # Update access time
        entry['last_access'] = datetime.now()
        entry['access_count'] += 1
        
        logger.debug(f"Cache hit for {sheet_name}")
        return entry['data']
    
    def put(self, file_path: str, sheet_name: str, data: pd.DataFrame) -> bool:
        """
        Store data in cache.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet
            data: DataFrame to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        key = self._generate_key(file_path, sheet_name)
        
        # Calculate data size
        data_size = data.memory_usage(deep=True).sum()
        
        # Check if single item exceeds max size
        if data_size > self._max_size_bytes:
            logger.warning(f"Data too large to cache: {data_size / 1024 / 1024:.2f}MB")
            return False
        
        # Evict old entries if necessary
        while self._current_size_bytes + data_size > self._max_size_bytes and self._cache:
            self._evict_lru()
        
        # Store in cache
        self._cache[key] = {
            'data': data,
            'timestamp': datetime.now(),
            'last_access': datetime.now(),
            'access_count': 0,
            'size': data_size
        }
        
        self._current_size_bytes += data_size
        logger.debug(f"Cached {sheet_name} ({data_size / 1024:.2f}KB)")
        
        return True
    
    def _remove(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self._cache:
            self._current_size_bytes -= self._cache[key]['size']
            del self._cache[key]
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['last_access']
        )
        
        logger.debug(f"Evicting LRU entry: {lru_key}")
        self._remove(lru_key)
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._current_size_bytes = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'entry_count': len(self._cache),
            'size_mb': self._current_size_bytes / 1024 / 1024,
            'max_size_mb': self._max_size_bytes / 1024 / 1024,
            'utilization_percentage': (self._current_size_bytes / self._max_size_bytes * 100) if self._max_size_bytes > 0 else 0
        }


class SheetManager:
    """Manages Excel sheet navigation and data access with caching."""
    
    def __init__(self, cache_ttl_minutes: int = 30, cache_max_size_mb: int = 100):
        """
        Initialize sheet manager.
        
        Args:
            cache_ttl_minutes: Cache time-to-live in minutes
            cache_max_size_mb: Maximum cache size in megabytes
        """
        self._cache = SheetCache(ttl_minutes=cache_ttl_minutes, max_size_mb=cache_max_size_mb)
        self._file_metadata: Dict[str, Dict[str, Any]] = {}
    
    def load_sheet(
        self, 
        file_path: str, 
        sheet_name: str,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Load a sheet from an Excel file with caching.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to load
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame containing sheet data
        """
        # Check cache first
        if use_cache:
            cached_data = self._cache.get(file_path, sheet_name)
            if cached_data is not None:
                return cached_data
        
        # Load from file
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Cache the data
            if use_cache:
                self._cache.put(file_path, sheet_name, df)
            
            logger.info(f"Loaded sheet '{sheet_name}' from {Path(file_path).name}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading sheet '{sheet_name}': {str(e)}")
            raise
    
    def get_all_sheets(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Load all sheets from an Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Dictionary mapping sheet names to DataFrames
        """
        try:
            # Get sheet names first
            sheet_names = self.get_sheet_names(file_path)
            
            # Load each sheet
            sheets = {}
            for sheet_name in sheet_names:
                sheets[sheet_name] = self.load_sheet(file_path, sheet_name)
            
            logger.info(f"Loaded {len(sheets)} sheets from {Path(file_path).name}")
            return sheets
            
        except Exception as e:
            logger.error(f"Error loading all sheets: {str(e)}")
            raise
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        Get list of sheet names in an Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            List of sheet names
        """
        try:
            xl_file = pd.ExcelFile(file_path)
            return [str(name) for name in xl_file.sheet_names]
        except Exception as e:
            logger.error(f"Error getting sheet names: {str(e)}")
            raise
    
    def switch_sheet(
        self, 
        file_path: str, 
        from_sheet: str, 
        to_sheet: str
    ) -> pd.DataFrame:
        """
        Switch from one sheet to another.
        
        Args:
            file_path: Path to Excel file
            from_sheet: Current sheet name (for context)
            to_sheet: Target sheet name
            
        Returns:
            DataFrame for target sheet
        """
        logger.debug(f"Switching from '{from_sheet}' to '{to_sheet}'")
        return self.load_sheet(file_path, to_sheet)
    
    def get_sheet_info(self, file_path: str, sheet_name: str) -> Dict[str, Any]:
        """
        Get metadata about a specific sheet.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet
            
        Returns:
            Dictionary with sheet information
        """
        df = self.load_sheet(file_path, sheet_name)
        
        return {
            'name': sheet_name,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            'has_missing_values': df.isnull().any().any(),
            'missing_percentage': float(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100) if len(df) > 0 else 0
        }
    
    def get_sheet_preview(
        self, 
        file_path: str, 
        sheet_name: str,
        page: int = 1,
        page_size: int = 5
    ) -> Dict[str, Any]:
        """
        Get a preview of sheet data with pagination.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet
            page: Page number (1-indexed)
            page_size: Number of rows per page
            
        Returns:
            Dictionary with preview data
        """
        df = self.load_sheet(file_path, sheet_name)
        
        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        preview_df = df.iloc[start_idx:end_idx]
        
        return {
            'columns': list(df.columns),
            'data': preview_df.fillna('').to_dict(orient='records'),
            'total_rows': len(df),
            'page': page,
            'page_size': page_size,
            'total_pages': (len(df) + page_size - 1) // page_size if len(df) > 0 else 0
        }
    
    def compare_sheets(
        self, 
        file_path: str, 
        sheet_name1: str, 
        sheet_name2: str
    ) -> Dict[str, Any]:
        """
        Compare two sheets in an Excel file.
        
        Args:
            file_path: Path to Excel file
            sheet_name1: First sheet name
            sheet_name2: Second sheet name
            
        Returns:
            Dictionary with comparison results
        """
        df1 = self.load_sheet(file_path, sheet_name1)
        df2 = self.load_sheet(file_path, sheet_name2)
        
        return {
            'sheet1': {
                'name': sheet_name1,
                'rows': len(df1),
                'columns': len(df1.columns),
                'column_names': list(df1.columns)
            },
            'sheet2': {
                'name': sheet_name2,
                'rows': len(df2),
                'columns': len(df2.columns),
                'column_names': list(df2.columns)
            },
            'comparison': {
                'same_columns': list(set(df1.columns) & set(df2.columns)),
                'unique_to_sheet1': list(set(df1.columns) - set(df2.columns)),
                'unique_to_sheet2': list(set(df2.columns) - set(df1.columns)),
                'row_difference': abs(len(df1) - len(df2))
            }
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.get_stats()
    
    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
    
    def preload_sheets(self, file_path: str, sheet_names: Optional[List[str]] = None) -> int:
        """
        Preload sheets into cache.
        
        Args:
            file_path: Path to Excel file
            sheet_names: List of sheet names to preload (None for all)
            
        Returns:
            Number of sheets preloaded
        """
        if sheet_names is None:
            sheet_names = self.get_sheet_names(file_path)
        
        loaded_count = 0
        for sheet_name in sheet_names:
            try:
                self.load_sheet(file_path, sheet_name, use_cache=True)
                loaded_count += 1
            except Exception as e:
                logger.warning(f"Failed to preload sheet '{sheet_name}': {str(e)}")
        
        logger.info(f"Preloaded {loaded_count}/{len(sheet_names)} sheets")
        return loaded_count
