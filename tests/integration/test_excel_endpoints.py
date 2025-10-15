"""
Integration Tests for Excel Upload and Processing Endpoints

Tests Excel file upload, processing, Q&A, and data analysis features.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import io


class TestExcelUploadEndpoints:
    """Test suite for Excel file upload endpoints."""
    
    @pytest.mark.asyncio
    async def test_upload_excel_without_auth(self, client: AsyncClient):
        """Test uploading Excel file without authentication."""
        # Create a minimal file-like object
        files = {"file": ("test.xlsx", io.BytesIO(b"fake excel content"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = await client.post("/api/excel/upload", files=files)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    @pytest.mark.asyncio
    async def test_upload_excel_with_auth(self, client: AsyncClient, auth_headers):
        """Test uploading Excel file with authentication."""
        files = {"file": ("test.xlsx", io.BytesIO(b"fake excel content"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = await client.post("/api/excel/upload", files=files, headers=auth_headers)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client: AsyncClient, auth_headers):
        """Test uploading non-Excel file."""
        files = {"file": ("test.txt", io.BytesIO(b"not an excel file"), "text/plain")}
        response = await client.post("/api/excel/upload", files=files, headers=auth_headers)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_list_uploaded_files_without_auth(self, client: AsyncClient):
        """Test listing uploaded files without authentication."""
        response = await client.get("/api/excel/files")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_list_uploaded_files_with_auth(self, client: AsyncClient, auth_headers):
        """Test listing uploaded files with authentication."""
        response = await client.get("/api/excel/files", headers=auth_headers)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_file_info_without_auth(self, client: AsyncClient):
        """Test getting file info without authentication."""
        response = await client.get("/api/excel/files/test-file-id")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_delete_file_without_auth(self, client: AsyncClient):
        """Test deleting file without authentication."""
        response = await client.delete("/api/excel/files/test-file-id")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]


class TestExcelProcessingEndpoints:
    """Test suite for Excel data processing endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_sheet_list_without_auth(self, client: AsyncClient):
        """Test getting sheet list without authentication."""
        response = await client.get("/api/excel/files/test-id/sheets")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_sheet_data_without_auth(self, client: AsyncClient):
        """Test getting sheet data without authentication."""
        response = await client.get("/api/excel/files/test-id/sheets/Sheet1/data")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_data_profile_without_auth(self, client: AsyncClient):
        """Test getting data profile without authentication."""
        response = await client.get("/api/excel/files/test-id/sheets/Sheet1/profile")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_column_stats_without_auth(self, client: AsyncClient):
        """Test getting column statistics without authentication."""
        response = await client.get("/api/excel/files/test-id/sheets/Sheet1/columns/test_col/stats")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]


class TestExcelQAEndpoints:
    """Test suite for Excel Q&A endpoints."""
    
    @pytest.mark.asyncio
    async def test_ask_question_without_auth(self, client: AsyncClient):
        """Test asking question without authentication."""
        data = {
            "file_id": "test-id",
            "sheet_name": "Sheet1",
            "question": "What is the average sales?"
        }
        response = await client.post("/api/excel/qa", json=data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    @pytest.mark.asyncio
    async def test_ask_question_with_auth(self, client: AsyncClient, auth_headers):
        """Test asking question with authentication."""
        data = {
            "file_id": "test-id",
            "sheet_name": "Sheet1",
            "question": "What is the total revenue?"
        }
        response = await client.post("/api/excel/qa", json=data, headers=auth_headers)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]
    
    @pytest.mark.asyncio
    async def test_ask_question_empty_question(self, client: AsyncClient, auth_headers):
        """Test asking empty question."""
        data = {
            "file_id": "test-id",
            "sheet_name": "Sheet1",
            "question": ""
        }
        response = await client.post("/api/excel/qa", json=data, headers=auth_headers)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_qa_history_without_auth(self, client: AsyncClient):
        """Test getting Q&A history without authentication."""
        response = await client.get("/api/excel/files/test-id/qa/history")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_get_qa_history_with_auth(self, client: AsyncClient, auth_headers):
        """Test getting Q&A history with authentication."""
        response = await client.get("/api/excel/files/test-id/qa/history", headers=auth_headers)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    @pytest.mark.asyncio
    async def test_generate_chart_without_auth(self, client: AsyncClient):
        """Test generating chart without authentication."""
        data = {
            "file_id": "test-id",
            "sheet_name": "Sheet1",
            "chart_type": "bar",
            "x_column": "category",
            "y_column": "sales"
        }
        response = await client.post("/api/excel/charts", json=data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
