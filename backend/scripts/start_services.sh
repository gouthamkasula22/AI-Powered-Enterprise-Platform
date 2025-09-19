#!/bin/bash

# Quick Start Script for User Authentication System
# This script sets up Docker containers for PostgreSQL and Redis

echo "🚀 Starting User Authentication System Services..."
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "🐳 Starting PostgreSQL and Redis containers..."

# Change to root directory to find docker-compose.yml
cd ..
docker-compose up -d
cd backend_new

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
cd ..
if docker-compose exec -T postgres pg_isready -U auth_user -d auth_db > /dev/null 2>&1; then
cd backend_new
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
    cd ..
    docker-compose logs postgres
    cd backend_new
    exit 1
fi

# Check Redis
cd ..
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    cd backend_new
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
    cd ..
    docker-compose logs redis
    cd backend_new
    exit 1
fi

echo ""
echo "🎉 All services are running!"
echo ""
echo "📊 Service URLs:"
echo "   PostgreSQL: localhost:5433"
echo "   Redis: localhost:6379"
echo "   pgAdmin (DB Admin): http://localhost:5050"
echo ""
echo "📝 pgAdmin Login:"
echo "   Email: admin@example.com"
echo "   Password: admin123"
echo ""
echo "📝 Next steps:"
echo "   1. Copy .env.example to .env"
echo "   2. Run: python scripts/setup_database.py"
echo "   3. Start the API: python scripts/run_dev_server.py"
echo ""
echo "🛑 To stop services: docker-compose down (from root directory)"