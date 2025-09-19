# FastAPI Presentation Layer - API Documentation

## Overview

The FastAPI Presentation Layer provides a complete HTTP API interface for the User Authentication System. It implements clean architecture principles by acting as the outermost layer that translates HTTP requests into domain operations and returns HTTP responses.

## Architecture Structure

```
src/presentation/
├── main.py                     # FastAPI application entry point
├── api/
│   ├── endpoints/              # API route definitions
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── users.py           # User management endpoints
│   │   └── health.py          # Health check endpoints
│   ├── middleware/             # Custom middleware
│   │   └── auth_middleware.py # Auth, rate limiting, logging middleware
│   ├── dependencies/           # Dependency injection
│   │   └── auth.py            # Authentication dependencies
│   ├── exception_handlers/     # Exception handling
│   │   └── handlers.py        # Domain/HTTP exception handlers
│   └── schemas/                # Pydantic models
│       └── auth.py            # API request/response schemas
└── run_dev_server.py          # Development server launcher
```

## Key Features

### 1. Complete Authentication API
- **POST /auth/register** - User registration with email verification
- **POST /auth/login** - User authentication with JWT tokens
- **POST /auth/logout** - Token invalidation
- **POST /auth/refresh** - Access token renewal
- **POST /auth/verify-email** - Email verification
- **POST /auth/forgot-password** - Password reset initiation
- **POST /auth/reset-password** - Password reset confirmation
- **POST /auth/change-password** - Password change (authenticated)

### 2. User Management API
- **GET /users/profile** - Get current user profile
- **PUT /users/profile** - Update user profile
- **DELETE /users/account** - Delete user account
- **GET /users/me** - Get current user info
- **GET /users/admin/users** - List all users (admin only)
- **GET /users/admin/users/{id}** - Get user by ID (admin only)
- **PATCH /users/admin/users/{id}/activate** - Activate user (admin only)
- **PATCH /users/admin/users/{id}/deactivate** - Deactivate user (admin only)
- **DELETE /users/admin/users/{id}** - Delete user (admin only)

### 3. Health Monitoring API
- **GET /health** - Basic health check
- **GET /health/detailed** - Detailed system health
- **GET /health/ready** - Readiness probe (Kubernetes)
- **GET /health/live** - Liveness probe (Kubernetes)

### 4. Advanced Middleware
- **AuthenticationMiddleware** - Security headers and auth processing
- **RateLimitMiddleware** - Request rate limiting with IP tracking
- **RequestLoggingMiddleware** - Comprehensive request/response logging
- **CORS Support** - Cross-origin resource sharing configuration

### 5. Comprehensive Exception Handling
- **Domain Exception Mapping** - Converts domain exceptions to HTTP status codes
- **Validation Error Handling** - Pydantic validation error formatting
- **General Exception Handling** - Catch-all with proper error responses
- **Development Debug Mode** - Enhanced error details in development

### 6. Security Features
- **JWT Authentication** - Bearer token-based authentication
- **Rate Limiting** - Configurable request limits per endpoint
- **CORS Protection** - Restricted cross-origin access
- **Security Headers** - XSS protection, content type sniffing prevention
- **Trusted Host Validation** - Host header validation

## API Documentation

### Authentication Flow
1. **Registration**: `POST /auth/register` → Email verification required
2. **Login**: `POST /auth/login` → Returns access + refresh tokens
3. **Protected Requests**: Include `Authorization: Bearer {access_token}` header
4. **Token Refresh**: `POST /auth/refresh` when access token expires
5. **Logout**: `POST /auth/logout` to invalidate tokens

### Response Format
All API responses follow a consistent format:

**Success Response:**
```json
{
  "user": {...},
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "message": "Operation successful"
}
```

**Error Response:**
```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "path": "/api/endpoint"
}
```

### Status Codes
- **200 OK** - Successful operation
- **201 Created** - Resource created successfully
- **400 Bad Request** - Validation error or invalid request
- **401 Unauthorized** - Authentication required or invalid credentials
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **409 Conflict** - Resource already exists
- **422 Unprocessable Entity** - Request validation failed
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Unexpected server error

## Development Setup

### 1. Install Dependencies
```bash
cd backend_new
pip install -r requirements.txt
```

### 2. Run Development Server
```bash
python run_dev_server.py
```

### 3. Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 4. Test Health Endpoints
- **Basic Health**: http://localhost:8000/health
- **Detailed Health**: http://localhost:8000/health/detailed

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-password

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

### Rate Limiting Configuration
```python
# In main.py
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Endpoint-specific limits in middleware
endpoint_limits = {
    "/auth/login": 5,          # 5 attempts per minute
    "/auth/register": 3,       # 3 attempts per minute
    "/auth/forgot-password": 3 # 3 attempts per minute
}
```

## Production Considerations

### 1. Security
- Use HTTPS in production
- Set secure JWT secret keys
- Configure proper CORS origins
- Enable trusted host validation
- Implement proper rate limiting with Redis

### 2. Performance
- Use connection pooling for database
- Implement Redis caching
- Configure proper logging levels
- Use async/await throughout

### 3. Monitoring
- Health check endpoints for load balancers
- Comprehensive logging with structured format
- Error tracking and alerting
- Performance metrics collection

### 4. Deployment
- Use production ASGI server (Gunicorn + Uvicorn)
- Configure proper environment variables
- Set up database migrations
- Implement graceful shutdown

## Integration with Clean Architecture

The FastAPI Presentation Layer maintains strict adherence to clean architecture:

1. **Dependency Direction**: Only depends on Application layer, never on Infrastructure
2. **Domain Independence**: No direct domain logic, only HTTP concerns
3. **Use Case Integration**: All business operations go through Application Use Cases
4. **Exception Translation**: Converts domain exceptions to HTTP responses
5. **Validation Separation**: Pydantic schemas for HTTP, DTOs for application layer

This ensures the API layer can be replaced without affecting business logic and maintains testability and maintainability.