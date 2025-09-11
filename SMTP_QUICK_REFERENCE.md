# SMTP Configuration Quick Reference

## File Locations

- **SMTP Test Script**: `tests/test_smtp.py` - For testing your email configuration
- **SMTP Configuration Helper**: `scripts/configure_smtp.py` - Interactive setup wizard  
- **Setup Guide**: `backend/SMTP_SETUP_GUIDE.md` - Comprehensive documentation
- **Configuration File**: `backend/.env` - Where your SMTP settings are stored

## Quick Commands

### Configure SMTP Settings
```bash
cd scripts
python configure_smtp.py
```

### Test SMTP Configuration  
```bash
cd tests
python test_smtp.py
```

### Start Backend Server
```bash
cd backend
python main.py
```

## Why These Locations?

- **`tests/`** - Contains testing utilities and test scripts
- **`scripts/`** - Contains utility scripts for setup and configuration
- **`backend/`** - Contains the main application code and configuration files

This organization follows Python project best practices and keeps testing utilities separate from production code.
