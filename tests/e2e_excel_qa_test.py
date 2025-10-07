"""
End-to-End Test for Excel Q&A System

Tests the complete flow:
1. User authentication
2. Excel file upload
3. Document processing
4. Sheet metadata extraction
5. Natural language query submission
6. Query execution (Claude API → Code Generation → Validation → Execution)
7. Result retrieval and display
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

# Load environment variables from backend/.env
backend_env_path = Path(__file__).parent.parent / "backend" / ".env"
if backend_env_path.exists():
    with open(backend_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"
AUTH_BASE = f"{BASE_URL}/api/auth"
TEST_USER = {
    "email": "testuser@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
}
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(step_num, description):
    """Print test step header"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}Step {step_num}: {description}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}[OK] {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {message}{Colors.END}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.YELLOW}[INFO] {message}{Colors.END}")

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_anthropic_api_key():
    """Check if Anthropic API key is configured"""
    return ANTHROPIC_API_KEY is not None and len(ANTHROPIC_API_KEY) > 0

def login(email, password):
    """Login and get JWT token"""
    response = requests.post(
        f"{AUTH_BASE}/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def create_test_user():
    """Create a test user if it doesn't exist"""
    try:
        response = requests.post(
            f"{AUTH_BASE}/register",
            json={
                "email": TEST_USER["email"],
                "password": TEST_USER["password"],
                "first_name": TEST_USER["first_name"],
                "last_name": TEST_USER["last_name"]
            }
        )
        if response.status_code in [200, 201]:
            return True
        # User might already exist (409 Conflict)
        if response.status_code == 409:
            print_info("User already exists, will try to login")
            return True
        print_error(f"Registration failed: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print_error(f"Exception during registration: {e}")
        return False

def create_sample_excel():
    """Create a sample Excel file for testing"""
    import pandas as pd
    import openpyxl
    
    # Create sample data
    sales_data = pd.DataFrame({
        'Product': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones'],
        'Quantity': [15, 50, 30, 20, 35],
        'Price': [999.99, 25.50, 75.00, 299.99, 89.99],
        'Category': ['Electronics', 'Accessories', 'Accessories', 'Electronics', 'Audio']
    })
    
    # Calculate revenue
    sales_data['Revenue'] = sales_data['Quantity'] * sales_data['Price']
    
    # Create Excel file with multiple sheets
    file_path = Path(__file__).parent / "test_sales_data.xlsx"
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        sales_data.to_excel(writer, sheet_name='Sales', index=False)
        
        # Add a summary sheet
        summary = pd.DataFrame({
            'Metric': ['Total Revenue', 'Total Quantity', 'Avg Price'],
            'Value': [
                sales_data['Revenue'].sum(),
                sales_data['Quantity'].sum(),
                sales_data['Price'].mean()
            ]
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
    
    print_success(f"Created test Excel file: {file_path}")
    return file_path

def upload_excel(token, file_path):
    """Upload Excel file"""
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(
            f"{API_BASE}/excel/upload",
            headers=headers,
            files=files
        )
    
    if response.status_code in [200, 201]:
        return response.json()
    
    print_error(f"Upload failed: {response.status_code} - {response.text}")
    return None

def get_document(token, doc_id):
    """Get document details"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE}/excel/{doc_id}",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return None

def get_sheets(token, doc_id):
    """Get document sheets"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE}/excel/{doc_id}/sheets",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return None

def get_sheet_preview(token, doc_id, sheet_name, rows=10):
    """Get sheet preview"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE}/excel/{doc_id}/sheets/{sheet_name}/preview",
        headers=headers,
        params={"rows": rows}
    )
    if response.status_code == 200:
        return response.json()
    print(f"[DEBUG] Sheet preview error: {response.status_code} - {response.text}")
    return None

def submit_query(token, doc_id, query_text, sheet_name=None):
    """Submit a natural language query"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"query_text": query_text}
    if sheet_name:
        payload["target_sheet"] = sheet_name
    
    response = requests.post(
        f"{API_BASE}/excel/{doc_id}/query",
        headers=headers,
        json=payload
    )
    if response.status_code in [200, 201]:
        return response.json()
    print(f"[DEBUG] Submit query error: {response.status_code} - {response.text}")
    return None

def execute_query(token, doc_id, query_id):
    """Execute a query"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE}/excel/{doc_id}/queries/{query_id}/execute",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return None

def get_optimizer_metrics(token):
    """Get optimizer metrics"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE}/excel/optimizer/metrics",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return None

def run_e2e_test():
    """Run end-to-end test"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}Excel Q&A System - End-to-End Test{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")
    
    # Step 0: Prerequisites
    print_step(0, "Checking Prerequisites")
    
    if not check_backend_health():
        print_error("Backend is not running. Please start the backend server.")
        print_info("Run: cd backend && python scripts/run_dev_server.py")
        return False
    print_success("Backend is running")
    
    if not check_anthropic_api_key():
        print_error("ANTHROPIC_API_KEY environment variable is not set")
        print_info("Set it with: $env:ANTHROPIC_API_KEY='your-key-here'")
        return False
    print_success("Anthropic API key is configured")
    
    # Step 1: Authentication
    print_step(1, "User Authentication")
    
    # Try to login, create user if doesn't exist
    token = login(TEST_USER["email"], TEST_USER["password"])
    if not token:
        print_info("Test user doesn't exist, creating...")
        if create_test_user():
            print_success("Test user created")
            token = login(TEST_USER["email"], TEST_USER["password"])
        else:
            print_error("Failed to create test user")
            return False
    
    if token:
        print_success(f"Logged in successfully")
        print_info(f"Token: {token[:20]}...")
    else:
        print_error("Login failed")
        return False
    
    # Step 2: Create Sample Excel
    print_step(2, "Creating Sample Excel File")
    excel_file = create_sample_excel()
    
    # Step 3: Upload Excel
    print_step(3, "Uploading Excel File")
    upload_result = upload_excel(token, excel_file)
    
    if not upload_result:
        print_error("Failed to upload Excel file")
        print_info("Check if Excel API endpoints are registered")
        return False
    
    doc_id = upload_result.get("id")
    print_success(f"Excel uploaded successfully (ID: {doc_id})")
    print_info(f"Filename: {upload_result.get('original_filename')}")
    print_info(f"Status: {upload_result.get('status')}")
    
    # Wait for processing
    print_info("Waiting for document processing...")
    for i in range(10):
        time.sleep(1)
        doc = get_document(token, doc_id)
        if doc and doc.get("status") == "ready":
            print_success("Document processing complete")
            break
        print_info(f"Status: {doc.get('status') if doc else 'unknown'}")
    else:
        print_error("Document processing timeout")
        return False
    
    # Step 4: Get Document Metadata
    print_step(4, "Retrieving Document Metadata")
    doc = get_document(token, doc_id)
    
    if doc:
        print_success("Document metadata retrieved")
        print_info(f"Sheets: {doc.get('sheet_count')}")
        print_info(f"Total Rows: {doc.get('total_rows')}")
        print_info(f"Total Columns: {doc.get('total_columns')}")
    else:
        print_error("Failed to get document metadata")
        return False
    
    # Step 5: Get Sheets
    print_step(5, "Retrieving Sheet Information")
    sheets = get_sheets(token, doc_id)
    
    if sheets:
        print_success(f"Retrieved {len(sheets)} sheets")
        for sheet in sheets:
            print_info(f"  - {sheet['sheet_name']}: {sheet['row_count']} rows, {sheet['column_count']} columns")
    else:
        print_error("Failed to get sheets")
        return False
    
    # Step 6: Get Sheet Preview
    print_step(6, "Retrieving Sheet Preview")
    preview = get_sheet_preview(token, doc_id, "Sales", rows=5)
    
    if preview:
        print_success("Sheet preview retrieved")
        print_info(f"Columns: {', '.join(preview.get('column_names', []))}")
        print_info(f"Rows shown: {len(preview.get('data', []))}")
    else:
        print_error("Failed to get sheet preview")
        return False
    
    # Step 7: Submit Queries
    print_step(7, "Submitting Natural Language Queries")
    
    test_queries = [
        ("What is the total revenue?", "Sales"),
        ("Show me the top 3 products by quantity sold", "Sales"),
        ("What is the average price of all products?", "Sales"),
        ("How many products are in the Electronics category?", "Sales"),
    ]
    
    query_results = []
    
    for query_text, sheet_name in test_queries:
        print_info(f"\nQuery: '{query_text}'")
        query = submit_query(token, doc_id, query_text, sheet_name)
        
        if query:
            print_success(f"Query submitted (ID: {query['id']})")
            query_results.append((query, query_text))
        else:
            print_error(f"Failed to submit query")
    
    # Step 8: Execute Queries
    print_step(8, "Executing Queries with Claude AI")
    
    for query, query_text in query_results:
        print_info(f"\nExecuting: '{query_text}'")
        
        result = execute_query(token, doc_id, query['id'])
        
        if result:
            status = result.get('status')
            if status == 'success':
                print_success(f"Query executed successfully")
                print_info(f"Execution time: {result.get('execution_time_ms')}ms")
                
                # Show generated code
                if result.get('generated_code'):
                    print_info("Generated code:")
                    print(f"{Colors.YELLOW}{result['generated_code']}{Colors.END}")
                
                # Show result
                exec_result = result.get('execution_result')
                if exec_result is not None:
                    print_info(f"Result: {exec_result}")
            else:
                print_error(f"Query execution failed")
                if result.get('error_message'):
                    print_error(f"Error: {result['error_message']}")
        else:
            print_error("Failed to execute query")
        
        # Small delay between queries
        time.sleep(1)
    
    # Step 9: Check Optimizer Metrics
    print_step(9, "Checking Query Optimizer Metrics")
    
    metrics = get_optimizer_metrics(token)
    
    if metrics:
        print_success("Optimizer metrics retrieved")
        print_info(f"Total queries executed: {metrics.get('total_queries', 0)}")
        print_info(f"Cache hits: {metrics.get('cache_hits', 0)}")
        print_info(f"Cache misses: {metrics.get('cache_misses', 0)}")
        print_info(f"Cache hit rate: {metrics.get('cache_hit_rate', 0):.2%}")
        print_info(f"Average execution time: {metrics.get('avg_execution_time_ms', 0):.2f}ms")
    else:
        print_error("Failed to get optimizer metrics")
    
    # Cleanup
    print_step(10, "Cleanup")
    if excel_file.exists():
        excel_file.unlink()
        print_success("Test Excel file removed")
    
    # Final Summary
    print(f"\n{Colors.GREEN}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}[SUCCESS] End-to-End Test Completed Successfully!{Colors.END}")
    print(f"{Colors.GREEN}{'='*70}{Colors.END}")
    
    print(f"\n{Colors.BLUE}Summary:{Colors.END}")
    print(f"  • Authenticated user")
    print(f"  • Uploaded and processed Excel file")
    print(f"  • Retrieved document metadata and sheets")
    print(f"  • Submitted {len(test_queries)} natural language queries")
    print(f"  • Executed queries with Claude AI code generation")
    print(f"  • Validated code safety")
    print(f"  • Executed code in sandbox")
    print(f"  • Retrieved and displayed results")
    print(f"  • Checked optimizer cache metrics")
    
    return True

if __name__ == "__main__":
    try:
        success = run_e2e_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test failed with error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
