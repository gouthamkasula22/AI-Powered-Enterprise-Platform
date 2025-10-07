"""
Unit Tests for Excel Processor

Tests for Excel file processing and metadata extraction.
"""

import pytest
import pandas as pd
from pathlib import Path
from backend.src.infrastructure.excel import ExcelProcessor


class TestExcelProcessor:
    """Test suite for ExcelProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create ExcelProcessor instance."""
        return ExcelProcessor()
    
    @pytest.fixture
    def sample_excel_file(self, tmp_path):
        """Create a sample Excel file for testing."""
        file_path = tmp_path / "test_data.xlsx"
        
        # Create sample data
        df1 = pd.DataFrame({
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Age': [25, 30, 35],
            'Salary': [50000, 60000, 70000]
        })
        
        df2 = pd.DataFrame({
            'Product': ['A', 'B', 'C'],
            'Price': [10.5, 20.0, 15.75],
            'Stock': [100, 50, 75]
        })
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='Employees', index=False)
            df2.to_excel(writer, sheet_name='Products', index=False)
        
        return str(file_path)
    
    @pytest.mark.asyncio
    async def test_process_file(self, processor, sample_excel_file):
        """Test processing an Excel file."""
        metadata = await processor.process_file(sample_excel_file, user_id=1)
        
        assert metadata is not None
        assert 'filename' in metadata
        assert 'sheets' in metadata
        assert len(metadata['sheets']) == 2
        assert metadata['total_rows'] == 6  # 3 + 3
        assert metadata['total_columns'] == 6  # 3 + 3
    
    @pytest.mark.asyncio
    async def test_process_sheet(self, processor, sample_excel_file):
        """Test processing a single sheet."""
        sheet_meta = await processor.process_sheet(sample_excel_file, 'Employees')
        
        assert sheet_meta['name'] == 'Employees'
        assert sheet_meta['rows'] == 3
        assert sheet_meta['columns'] == 3
        assert 'Name' in sheet_meta['column_names']
        assert 'Age' in sheet_meta['column_names']
        assert 'Salary' in sheet_meta['column_names']
    
    @pytest.mark.asyncio
    async def test_get_sheet_preview(self, processor, sample_excel_file):
        """Test getting sheet preview."""
        preview = await processor.get_sheet_preview(
            sample_excel_file,
            'Employees',
            rows=2
        )
        
        assert preview['sheet_name'] == 'Employees'
        assert preview['rows'] == 3
        assert preview['columns'] == 3
        assert preview['preview_size'] == 2
        assert len(preview['data']) == 2
    
    @pytest.mark.asyncio
    async def test_get_sheet_data(self, processor, sample_excel_file):
        """Test getting paginated sheet data."""
        df = await processor.get_sheet_data(
            sample_excel_file,
            'Products',
            start_row=0,
            max_rows=2
        )
        
        assert len(df) == 2
        assert 'Product' in df.columns
        assert 'Price' in df.columns
        assert 'Stock' in df.columns
    
    @pytest.mark.asyncio
    async def test_invalid_file(self, processor):
        """Test handling invalid file."""
        with pytest.raises(Exception):
            await processor.process_file('nonexistent.xlsx', user_id=1)
    
    @pytest.mark.asyncio
    async def test_invalid_sheet(self, processor, sample_excel_file):
        """Test handling invalid sheet name."""
        with pytest.raises(Exception):
            await processor.process_sheet(sample_excel_file, 'NonExistentSheet')
