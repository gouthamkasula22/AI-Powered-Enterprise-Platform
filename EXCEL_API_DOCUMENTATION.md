# Excel Q&A Assistant API Documentation

## Overview

The Excel Q&A Assistant API provides endpoints for uploading, analyzing, and querying Excel files using natural language. This API is part of the User Authentication System and requires authentication.

**Base URL**: `/api/v1/excel`

**Authentication**: All endpoints require a valid JWT token in the `Authorization` header.

---

## Endpoints

### 1. Upload Excel File

Upload an Excel file for processing and analysis.

**Endpoint**: `POST /api/v1/excel/upload`

**Headers**:
```
Authorization: Bearer <your_jwt_token>
Content-Type: multipart/form-data
```

**Request Body**:
- `file`: Excel file (.xlsx, .xls, .xlsm) - Max 50MB

**Response** (201 Created):
```json
{
  "id": 1,
  "user_id": 123,
  "filename": "123_20251006_145632_sales_data.xlsx",
  "original_filename": "sales_data.xlsx",
  "file_size": 1048576,
  "sheet_count": 3,
  "total_rows": 1500,
  "total_columns": 12,
  "status": "ready",
  "error_message": null,
  "uploaded_at": "2025-10-06T14:56:32.123Z",
  "processed_at": "2025-10-06T14:56:35.456Z",
  "last_accessed_at": null
}
```

**Error Responses**:
- `400 Bad Request`: Invalid file format or missing file
- `413 Payload Too Large`: File exceeds 50MB limit
- `401 Unauthorized`: Missing or invalid authentication token

---

### 2. Get User Documents

Retrieve all Excel documents for the authenticated user.

**Endpoint**: `GET /api/v1/excel/documents`

**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 50, max: 100)

**Response** (200 OK):
```json
{
  "documents": [
    {
      "id": 1,
      "user_id": 123,
      "filename": "123_20251006_145632_sales_data.xlsx",
      "original_filename": "sales_data.xlsx",
      "file_size": 1048576,
      "sheet_count": 3,
      "total_rows": 1500,
      "total_columns": 12,
      "status": "ready",
      "uploaded_at": "2025-10-06T14:56:32.123Z",
      "processed_at": "2025-10-06T14:56:35.456Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

---

### 3. Get Document Details

Retrieve details of a specific Excel document.

**Endpoint**: `GET /api/v1/excel/{document_id}`

**Path Parameters**:
- `document_id`: Document ID (integer)

**Response** (200 OK):
```json
{
  "id": 1,
  "user_id": 123,
  "filename": "123_20251006_145632_sales_data.xlsx",
  "original_filename": "sales_data.xlsx",
  "file_size": 1048576,
  "sheet_count": 3,
  "total_rows": 1500,
  "total_columns": 12,
  "status": "ready",
  "uploaded_at": "2025-10-06T14:56:32.123Z",
  "processed_at": "2025-10-06T14:56:35.456Z",
  "last_accessed_at": "2025-10-06T15:30:00.000Z"
}
```

**Error Responses**:
- `404 Not Found`: Document not found or user doesn't have access

---

### 4. Get Document Sheets

Retrieve all sheets within an Excel document.

**Endpoint**: `GET /api/v1/excel/{document_id}/sheets`

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "document_id": 1,
    "sheet_name": "Sales Q1",
    "sheet_index": 0,
    "row_count": 500,
    "column_count": 8,
    "columns": ["Date", "Product", "Quantity", "Price", "Total", "Region", "Salesperson", "Notes"],
    "column_types": {
      "Date": "datetime64[ns]",
      "Product": "object",
      "Quantity": "int64",
      "Price": "float64",
      "Total": "float64",
      "Region": "object",
      "Salesperson": "object",
      "Notes": "object"
    },
    "statistics": {
      "row_count": 500,
      "column_count": 8,
      "summary": {
        "total_cells": 4000,
        "total_missing": 25,
        "missing_percentage": 0.625,
        "duplicate_rows": 0
      },
      "columns": {
        "Price": {
          "data_type": "numeric",
          "min": 9.99,
          "max": 999.99,
          "mean": 125.50,
          "median": 99.99,
          "std": 45.30
        }
      }
    },
    "semantic_types": {
      "Date": "datetime",
      "Product": "categorical",
      "Quantity": "numeric",
      "Price": "numeric",
      "Total": "numeric",
      "Region": "categorical",
      "Salesperson": "text",
      "Notes": "text"
    },
    "key_columns": [],
    "has_missing_values": true,
    "missing_percentage": 1,
    "duplicate_rows": 0,
    "created_at": "2025-10-06T14:56:35.123Z",
    "updated_at": "2025-10-06T14:56:35.123Z"
  }
]
```

---

### 5. Get Sheet Preview

Get a preview of data from a specific sheet.

**Endpoint**: `GET /api/v1/excel/{document_id}/sheets/{sheet_name}/preview`

**Path Parameters**:
- `document_id`: Document ID (integer)
- `sheet_name`: Sheet name (string)

**Query Parameters**:
- `rows`: Number of rows to preview (default: 10, min: 1, max: 100)

**Response** (200 OK):
```json
{
  "sheet_name": "Sales Q1",
  "rows": 500,
  "columns": 8,
  "column_names": ["Date", "Product", "Quantity", "Price", "Total", "Region", "Salesperson", "Notes"],
  "data": [
    {
      "Date": "2025-01-01",
      "Product": "Widget A",
      "Quantity": 10,
      "Price": 19.99,
      "Total": 199.90,
      "Region": "North",
      "Salesperson": "John Doe",
      "Notes": null
    },
    {
      "Date": "2025-01-02",
      "Product": "Widget B",
      "Quantity": 5,
      "Price": 29.99,
      "Total": 149.95,
      "Region": "South",
      "Salesperson": "Jane Smith",
      "Notes": "Express delivery"
    }
  ],
  "preview_size": 10
}
```

---

### 6. Delete Document

Delete an Excel document and all associated data.

**Endpoint**: `DELETE /api/v1/excel/{document_id}`

**Response** (204 No Content): Empty response

**Error Responses**:
- `404 Not Found`: Document not found

---

### 7. Create Query

Submit a natural language query for Excel data analysis.

**Endpoint**: `POST /api/v1/excel/{document_id}/query`

**Request Body**:
```json
{
  "query_text": "What are the total sales by region?",
  "target_sheet": "Sales Q1"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "document_id": 1,
  "user_id": 123,
  "query_text": "What are the total sales by region?",
  "query_type": null,
  "target_sheet": "Sales Q1",
  "generated_code": null,
  "code_explanation": null,
  "status": "pending",
  "result": null,
  "error_message": null,
  "execution_time_ms": null,
  "created_at": "2025-10-06T15:30:00.000Z",
  "executed_at": null
}
```

**Fields**:
- `query_text`: Natural language question (required, 1-1000 characters)
- `target_sheet`: Specific sheet to query (optional)

---

### 8. Get Query History

Retrieve query history for a document.

**Endpoint**: `GET /api/v1/excel/{document_id}/queries`

**Query Parameters**:
- `limit`: Maximum queries to return (default: 20, max: 100)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "document_id": 1,
    "user_id": 123,
    "query_text": "What are the total sales by region?",
    "query_type": "analysis",
    "target_sheet": "Sales Q1",
    "generated_code": "df.groupby('Region')['Total'].sum()",
    "code_explanation": "Groups data by Region and calculates sum of Total column",
    "status": "success",
    "result": {
      "North": 50000.00,
      "South": 45000.00,
      "East": 55000.00,
      "West": 48000.00
    },
    "error_message": null,
    "execution_time_ms": 125,
    "created_at": "2025-10-06T15:30:00.000Z",
    "executed_at": "2025-10-06T15:30:01.125Z"
  }
]
```

---

### 9. Get Cache Statistics

Get cache statistics (for debugging/monitoring).

**Endpoint**: `GET /api/v1/excel/cache/stats`

**Response** (200 OK):
```json
{
  "entry_count": 5,
  "size_mb": 25.5,
  "max_size_mb": 100.0,
  "utilization_percentage": 25.5
}
```

---

### 10. Clear Cache

Clear the sheet cache (for debugging/monitoring).

**Endpoint**: `POST /api/v1/excel/cache/clear`

**Response** (204 No Content): Empty response

---

## Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **204 No Content**: Deletion successful
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid authentication
- **404 Not Found**: Resource not found
- **413 Payload Too Large**: File exceeds size limit
- **500 Internal Server Error**: Server error

---

## Document Status Values

- `uploaded`: File uploaded, processing not started
- `processing`: File is being processed
- `ready`: Processing complete, ready for queries
- `error`: Processing failed (see `error_message`)

---

## Query Status Values

- `pending`: Query submitted, execution pending
- `success`: Query executed successfully
- `error`: Query execution failed (see `error_message`)

---

## Example Usage

### Upload and Query Workflow

```python
import requests

# 1. Authenticate
auth_response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"email": "user@example.com", "password": "password"}
)
token = auth_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Upload Excel file
with open("sales_data.xlsx", "rb") as f:
    upload_response = requests.post(
        "http://localhost:8000/api/v1/excel/upload",
        headers=headers,
        files={"file": f}
    )
document = upload_response.json()
doc_id = document["id"]

# 3. Get sheets
sheets_response = requests.get(
    f"http://localhost:8000/api/v1/excel/{doc_id}/sheets",
    headers=headers
)
sheets = sheets_response.json()

# 4. Preview first sheet
preview_response = requests.get(
    f"http://localhost:8000/api/v1/excel/{doc_id}/sheets/{sheets[0]['sheet_name']}/preview",
    headers=headers,
    params={"rows": 5}
)
preview = preview_response.json()

# 5. Submit query
query_response = requests.post(
    f"http://localhost:8000/api/v1/excel/{doc_id}/query",
    headers=headers,
    json={
        "query_text": "What are the total sales by region?",
        "target_sheet": sheets[0]['sheet_name']
    }
)
query = query_response.json()
```

---

## Rate Limits

- **Upload**: 10 files per hour per user
- **Queries**: 100 queries per hour per user
- **File Size**: Maximum 50MB per file

---

## Supported File Formats

- `.xlsx` - Excel 2007+ (OpenXML)
- `.xls` - Excel 97-2003
- `.xlsm` - Excel Macro-Enabled

---

## Notes

- All datetime values are in ISO 8601 format (UTC)
- File uploads are processed asynchronously
- Check `status` field to verify processing completion
- Cached sheets expire after 30 minutes of inactivity
- Cache has a 100MB size limit (LRU eviction)
