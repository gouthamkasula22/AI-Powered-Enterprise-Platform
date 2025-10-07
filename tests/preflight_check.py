"""
Pre-Flight Check Script for Excel Q&A System

Verifies all dependencies and configurations before running tests.
"""

import os
import sys
import subprocess
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

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def check_mark(passed):
    return f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    required = (3, 10)
    passed = version >= required
    
    print(f"{check_mark(passed)} Python {version.major}.{version.minor}.{version.micro}")
    if not passed:
        print(f"  {Colors.RED}Required: Python {required[0]}.{required[1]} or higher{Colors.END}")
    return passed

def check_file_exists(path):
    """Check if file exists"""
    return Path(path).exists()

def check_package_installed(package):
    """Check if Python package is installed"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def check_env_variable(var_name):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    return value is not None and len(value) > 0

def check_port_available(port):
    """Check if port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0  # Port is available if connection fails

def run_preflight_checks():
    """Run all pre-flight checks"""
    print_header("Excel Q&A System - Pre-Flight Check")
    
    all_passed = True
    
    # Check 1: Python Version
    print(f"\n{Colors.YELLOW}1. Python Version{Colors.END}")
    passed = check_python_version()
    all_passed = all_passed and passed
    
    # Check 2: Required Files
    print(f"\n{Colors.YELLOW}2. Required Files{Colors.END}")
    required_files = [
        "backend/src/application/use_cases/excel/query_processor.py",
        "backend/src/infrastructure/excel/code_validator.py",
        "backend/src/infrastructure/excel/code_executor.py",
        "backend/src/application/use_cases/excel/query_optimizer.py",
        "frontend/src/components/excel/QueryInput.jsx",
        "frontend/src/components/excel/QueryHistory.jsx",
        "frontend/src/components/excel/ResultVisualization.jsx",
        "frontend/src/services/excel/excelService.js",
    ]
    
    for file_path in required_files:
        exists = check_file_exists(file_path)
        print(f"{check_mark(exists)} {file_path}")
        all_passed = all_passed and exists
    
    # Check 3: Python Dependencies
    print(f"\n{Colors.YELLOW}3. Python Dependencies{Colors.END}")
    python_packages = [
        "fastapi",
        "sqlalchemy",
        "pandas",
        "openpyxl",
        "anthropic",
        "numpy",
        "uvicorn",
        "pydantic",
    ]
    
    for package in python_packages:
        installed = check_package_installed(package)
        print(f"{check_mark(installed)} {package}")
        if not installed:
            all_passed = False
    
    # Check 4: Environment Variables
    print(f"\n{Colors.YELLOW}4. Environment Variables{Colors.END}")
    env_vars = {
        "ANTHROPIC_API_KEY": "Required for Claude AI integration",
        "DATABASE_URL": "Database connection (optional, defaults to SQLite)",
    }
    
    for var, description in env_vars.items():
        is_set = check_env_variable(var)
        status = check_mark(is_set) if var == "ANTHROPIC_API_KEY" else f"{Colors.BLUE}ℹ{Colors.END}"
        print(f"{status} {var}: {description}")
        if var == "ANTHROPIC_API_KEY":
            all_passed = all_passed and is_set
            if is_set:
                key = os.getenv(var)
                if key:
                    print(f"     Value: {key[:10]}...{key[-4:] if len(key) > 14 else ''}")
    
    # Check 5: Ports
    print(f"\n{Colors.YELLOW}5. Port Availability{Colors.END}")
    ports = {
        8000: "Backend API",
        5173: "Frontend Dev Server",
    }
    
    for port, service in ports.items():
        available = check_port_available(port)
        print(f"{check_mark(available)} Port {port} ({service})")
        if not available:
            print(f"  {Colors.YELLOW}Warning: Port {port} is in use. Service may already be running.{Colors.END}")
    
    # Check 6: Node.js (for frontend)
    print(f"\n{Colors.YELLOW}6. Node.js & NPM{Colors.END}")
    try:
        node_version = subprocess.check_output(["node", "--version"], stderr=subprocess.DEVNULL, text=True).strip()
        print(f"{Colors.GREEN}✓{Colors.END} Node.js {node_version}")
        
        npm_version = subprocess.check_output(["npm", "--version"], stderr=subprocess.DEVNULL, text=True).strip()
        print(f"{Colors.GREEN}✓{Colors.END} npm {npm_version}")
    except:
        print(f"{Colors.RED}✗{Colors.END} Node.js or npm not found")
        all_passed = False
    
    # Check 7: Frontend Dependencies
    print(f"\n{Colors.YELLOW}7. Frontend Dependencies{Colors.END}")
    node_modules_exists = check_file_exists("frontend/node_modules")
    print(f"{check_mark(node_modules_exists)} node_modules installed")
    if not node_modules_exists:
        print(f"  {Colors.YELLOW}Run: cd frontend && npm install{Colors.END}")
    
    # Check 8: Database
    print(f"\n{Colors.YELLOW}8. Database{Colors.END}")
    db_file_exists = check_file_exists("backend/user_auth.db")
    print(f"{check_mark(db_file_exists)} SQLite database file")
    if not db_file_exists:
        print(f"  {Colors.YELLOW}Run: cd backend && python scripts/setup_database.py{Colors.END}")
    
    # Final Summary
    print_header("Summary")
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All critical checks passed!{Colors.END}")
        print(f"\n{Colors.GREEN}Ready to run end-to-end tests.{Colors.END}")
        print(f"\n{Colors.BLUE}Next Steps:{Colors.END}")
        print(f"  1. Start backend:  cd backend && python scripts/run_dev_server.py")
        print(f"  2. Start frontend: cd frontend && npm run dev")
        print(f"  3. Run tests:      cd tests && python e2e_excel_qa_test.py")
        return True
    else:
        print(f"{Colors.RED}✗ Some checks failed. Please fix the issues above.{Colors.END}")
        return False

if __name__ == "__main__":
    try:
        success = run_preflight_checks()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n{Colors.RED}Error during pre-flight check: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
