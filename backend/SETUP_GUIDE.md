# Database and Redis Setup Guide

This guide will help you set up PostgreSQL and Redis for the User Authentication System.

## Prerequisites

- Docker Desktop (recommended for easy setup)
- OR PostgreSQL and Redis installed locally

## Option 1: Docker Setup (Recommended)

### 1. Create Docker Compose File

Create a `docker-compose.yml` file in the project root:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: auth_postgres
    environment:
      POSTGRES_DB: user_auth_db
      POSTGRES_USER: auth_user
      POSTGRES_PASSWORD: auth_password_123
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U auth_user -d user_auth_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: auth_redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  adminer:
    image: adminer
    container_name: auth_adminer
    ports:
      - "8080:8080"
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs postgres
docker-compose logs redis
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://auth_user:auth_password_123@localhost:5432/user_auth_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=user_auth_db
DB_USER=auth_user
DB_PASSWORD=auth_password_123

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration (for development - optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Application Configuration
DEBUG=True
ENVIRONMENT=development
```

## Option 2: Local Installation

### PostgreSQL Setup

#### Windows (using PostgreSQL installer):
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Install with these settings:
   - Username: `postgres`
   - Password: `your_password`
   - Port: `5432`
3. Create database:
```sql
CREATE DATABASE user_auth_db;
CREATE USER auth_user WITH PASSWORD 'auth_password_123';
GRANT ALL PRIVILEGES ON DATABASE user_auth_db TO auth_user;
```

#### macOS (using Homebrew):
```bash
brew install postgresql
brew services start postgresql
createdb user_auth_db
createuser -s auth_user
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres createdb user_auth_db
sudo -u postgres createuser auth_user
```

### Redis Setup

#### Windows:
1. Download Redis from https://redis.io/download
2. Or use WSL2 with Ubuntu and install Redis there

#### macOS:
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## Database Initialization

### 1. Install Python Dependencies

```bash
cd backend_new
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
# Test database connection
python scripts/test_database_integration.py

# Initialize database schema
python -c "
import asyncio
from src.infrastructure.database.database import initialize_database
asyncio.run(initialize_database())
print('Database initialized successfully!')
"
```

### 3. Verify Setup

```bash
# Test complete integration
python scripts/test_app_startup.py
```

## Database Management

### Access Database (Docker)

```bash
# Using docker exec
docker exec -it auth_postgres psql -U auth_user -d user_auth_db

# Using Adminer web interface
# Open http://localhost:8080
# System: PostgreSQL
# Server: postgres
# Username: auth_user
# Password: auth_password_123
# Database: user_auth_db
```

### Common Database Commands

```sql
-- View all tables
\dt

-- Describe user table
\d users

-- View users
SELECT * FROM users;

-- Check database size
SELECT pg_size_pretty(pg_database_size('user_auth_db'));
```

### Redis Management

```bash
# Connect to Redis (Docker)
docker exec -it auth_redis redis-cli

# Connect to Redis (Local)
redis-cli

# Common Redis commands
PING
INFO
KEYS *
FLUSHALL  # Clear all data (development only!)
```

## Troubleshooting

### Database Connection Issues

1. **Check if PostgreSQL is running:**
```bash
# Docker
docker-compose ps

# Local (Windows)
services.msc -> PostgreSQL

# Local (macOS/Linux)
brew services list | grep postgresql
sudo systemctl status postgresql
```

2. **Test connection:**
```bash
# Using psql
psql -h localhost -p 5432 -U auth_user -d user_auth_db

# Using Python
python -c "
import asyncio
import asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://auth_user:auth_password_123@localhost:5432/user_auth_db')
    print('Connected successfully!')
    await conn.close()
asyncio.run(test())
"
```

### Redis Connection Issues

1. **Check if Redis is running:**
```bash
# Docker
docker-compose ps

# Local
redis-cli ping
```

2. **Test connection:**
```bash
# Command line
redis-cli -h localhost -p 6379 ping

# Python
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
print(r.ping())
"
```

### Common Fixes

1. **Port conflicts:** Change ports in docker-compose.yml
2. **Permission denied:** Check user permissions and passwords
3. **Connection refused:** Ensure services are running and ports are open

## Running the Application

Once everything is set up:

```bash
# Start the development server
python scripts/run_dev_server.py

# Or using uvicorn directly
uvicorn src.presentation.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Production Notes

For production deployment:
1. Use strong passwords and secret keys
2. Enable SSL/TLS for database connections
3. Configure Redis with authentication
4. Use environment-specific configuration files
5. Set up database backups
6. Configure monitoring and logging