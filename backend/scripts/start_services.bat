@echo off
REM Quick Start Script for User Authentication System (Windows)
REM This script sets up Docker containers for PostgreSQL and Redis

echo 🚀 Starting User Authentication System Services...
echo ==================================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo 🐳 Starting PostgreSQL and Redis containers...

REM Change to root directory to find docker-compose.yml
cd ..
docker-compose up -d
cd backend_new

echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo 🔍 Checking service health...

REM Check PostgreSQL
cd ..
docker-compose exec -T postgres pg_isready -U auth_user -d auth_db >nul 2>&1
cd backend_new
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL is ready
) else (
    echo ❌ PostgreSQL is not ready
    docker-compose logs postgres
    pause
    exit /b 1
)

REM Check Redis
cd ..
docker-compose exec -T redis redis-cli ping >nul 2>&1
cd backend_new
if %errorlevel% equ 0 (
    echo ✅ Redis is ready
) else (
    echo ❌ Redis is not ready
    docker-compose logs redis
    pause
    exit /b 1
)

echo.
echo 🎉 All services are running!
echo.
echo 📊 Service URLs:
echo    PostgreSQL: localhost:5433
echo    Redis: localhost:6379
echo    pgAdmin (DB Admin): http://localhost:5050
echo.
echo 📝 pgAdmin Login:
echo    Email: admin@example.com
echo    Password: admin123
echo.
echo 📝 Next steps:
echo    1. Copy .env.example to .env
echo    2. Run: python scripts\setup_database.py
echo    3. Start the API: python scripts\run_dev_server.py
echo.
echo 🛑 To stop services: docker-compose down (from root directory)
echo.
pause