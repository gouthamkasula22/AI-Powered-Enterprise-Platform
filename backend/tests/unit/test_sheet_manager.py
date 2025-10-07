"""
Unit Tests for Sheet Manager

Tests for multi-sheet navigation and caching.
"""

import pytest
import pandas as pd
from backend.src.infrastructure.excel import SheetManager, SheetCache


class TestSheetCache:
    """Test suite for SheetCache."""
    
    @pytest.fixture
    def cache(self):
        """Create SheetCache instance."""
        return SheetCache(ttl_minutes=5, max_size_mb=10)
    
    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame."""
        return pd.DataFrame({'col': [1, 2, 3, 4, 5]})
    
    def test_put_and_get(self, cache, sample_data):
        """Test basic cache operations."""
        file_path = "/path/to/file.xlsx"
        sheet_name = "Sheet1"
        
        # Put data in cache
        success = cache.put(file_path, sheet_name, sample_data)
        assert success
        
        # Retrieve data
        cached_data = cache.get(file_path, sheet_name)
        assert cached_data is not None
        pd.testing.assert_frame_equal(cached_data, sample_data)
    
    def test_cache_miss(self, cache):
        """Test cache miss."""
        result = cache.get("/nonexistent.xlsx", "Sheet1")
        assert result is None
    
    def test_cache_stats(self, cache, sample_data):
        """Test cache statistics."""
        cache.put("/file.xlsx", "Sheet1", sample_data)
        
        stats = cache.get_stats()
        assert stats['entry_count'] == 1
        assert stats['size_mb'] > 0
        assert stats['utilization_percentage'] > 0
    
    def test_clear_cache(self, cache, sample_data):
        """Test cache clearing."""
        cache.put("/file.xlsx", "Sheet1", sample_data)
        assert cache.get_stats()['entry_count'] == 1
        
        cache.clear()
        assert cache.get_stats()['entry_count'] == 0
        assert cache.get("/file.xlsx", "Sheet1") is None
    
    def test_lru_eviction(self, cache):
        """Test LRU eviction when cache is full."""
        # Create small cache (1MB)
        small_cache = SheetCache(ttl_minutes=5, max_size_mb=1)
        
        # Add multiple large DataFrames
        for i in range(5):
            df = pd.DataFrame({
                'data': ['x' * 1000] * 1000  # ~1MB of data
            })
            small_cache.put(f"/file{i}.xlsx", "Sheet1", df)
        
        # Due to size limits, not all will be cached
        stats = small_cache.get_stats()
        assert stats['entry_count'] < 5


class TestSheetManager:
    """Test suite for SheetManager."""
    
    @pytest.fixture
    def manager(self):
        """Create SheetManager instance."""
        return SheetManager(cache_ttl_minutes=5, cache_max_size_mb=10)
    
    @pytest.fixture
    def sample_excel_file(self, tmp_path):
        """Create a sample Excel file."""
        file_path = tmp_path / "test.xlsx"
        
        df1 = pd.DataFrame({'A': [1, 2, 3]})
        df2 = pd.DataFrame({'B': [4, 5, 6]})
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='Sheet1', index=False)
            df2.to_excel(writer, sheet_name='Sheet2', index=False)
        
        return str(file_path)
    
    def test_load_sheet(self, manager, sample_excel_file):
        """Test loading a single sheet."""
        df = manager.load_sheet(sample_excel_file, 'Sheet1')
        
        assert df is not None
        assert 'A' in df.columns
        assert len(df) == 3
    
    def test_load_sheet_with_cache(self, manager, sample_excel_file):
        """Test that caching works."""
        # Load twice
        df1 = manager.load_sheet(sample_excel_file, 'Sheet1', use_cache=True)
        df2 = manager.load_sheet(sample_excel_file, 'Sheet1', use_cache=True)
        
        # Should get same data
        pd.testing.assert_frame_equal(df1, df2)
        
        # Cache should have 1 entry
        stats = manager.get_cache_stats()
        assert stats['entry_count'] >= 1
    
    def test_get_sheet_names(self, manager, sample_excel_file):
        """Test getting sheet names."""
        sheet_names = manager.get_sheet_names(sample_excel_file)
        
        assert len(sheet_names) == 2
        assert 'Sheet1' in sheet_names
        assert 'Sheet2' in sheet_names
    
    def test_get_all_sheets(self, manager, sample_excel_file):
        """Test loading all sheets."""
        sheets = manager.get_all_sheets(sample_excel_file)
        
        assert len(sheets) == 2
        assert 'Sheet1' in sheets
        assert 'Sheet2' in sheets
        assert 'A' in sheets['Sheet1'].columns
        assert 'B' in sheets['Sheet2'].columns
    
    def test_switch_sheet(self, manager, sample_excel_file):
        """Test switching between sheets."""
        df = manager.switch_sheet(
            sample_excel_file,
            from_sheet='Sheet1',
            to_sheet='Sheet2'
        )
        
        assert 'B' in df.columns
    
    def test_get_sheet_info(self, manager, sample_excel_file):
        """Test getting sheet metadata."""
        info = manager.get_sheet_info(sample_excel_file, 'Sheet1')
        
        assert info['name'] == 'Sheet1'
        assert info['row_count'] == 3
        assert info['column_count'] == 1
        assert 'A' in info['columns']
    
    def test_compare_sheets(self, manager, sample_excel_file):
        """Test comparing two sheets."""
        comparison = manager.compare_sheets(
            sample_excel_file,
            'Sheet1',
            'Sheet2'
        )
        
        assert comparison['sheet1']['name'] == 'Sheet1'
        assert comparison['sheet2']['name'] == 'Sheet2'
        assert comparison['comparison']['row_difference'] == 0
    
    def test_preload_sheets(self, manager, sample_excel_file):
        """Test preloading sheets into cache."""
        loaded_count = manager.preload_sheets(sample_excel_file)
        
        assert loaded_count == 2
        
        # Verify cache has entries
        stats = manager.get_cache_stats()
        assert stats['entry_count'] == 2
    
    def test_clear_manager_cache(self, manager, sample_excel_file):
        """Test clearing manager cache."""
        manager.load_sheet(sample_excel_file, 'Sheet1')
        assert manager.get_cache_stats()['entry_count'] > 0
        
        manager.clear_cache()
        assert manager.get_cache_stats()['entry_count'] == 0
    
    def test_invalid_sheet(self, manager, sample_excel_file):
        """Test handling invalid sheet name."""
        with pytest.raises(Exception):
            manager.load_sheet(sample_excel_file, 'NonExistentSheet')
