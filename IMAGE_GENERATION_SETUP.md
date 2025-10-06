# Image Generation Feature Setup Guide

This guide covers the setup and configuration for the AI Image Generation feature using DALL-E 3.

## 🎯 Feature Overview

The image generation feature provides:
- **DALL-E 3 Integration**: High-quality AI image generation
- **Async Processing**: Background task processing with Celery + Redis
- **Chat Integration**: Generate images directly in chat with `/image` command
- **Gallery Management**: Organize images in collections
- **Real-time Progress**: Live updates during generation
- **Cost Tracking**: Monitor API usage and costs

## 🔧 Prerequisites

### Backend Requirements

1. **OpenAI API Key**: 
   ```bash
   # Add to your .env file
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

2. **Redis Server**: Required for Celery task queue
   ```bash
   # Install Redis (Windows with WSL or Docker)
   docker run -d -p 6379:6379 --name redis redis:alpine
   
   # Or install directly (Linux/Mac)
   # Ubuntu: sudo apt install redis-server
   # Mac: brew install redis
   ```

3. **Celery Worker**: Background task processing
   ```bash
   # Start Celery worker (in backend directory)
   celery -A src.infrastructure.tasks.celery_app worker --loglevel=info
   ```

### Environment Variables

Add these to your `backend/.env` file:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0

# Image Generation Settings
DALLE_MODEL=dall-e-3
DALLE_MAX_RETRIES=3
DALLE_TIMEOUT_SECONDS=60
IMAGE_GENERATION_ENABLED=true

# Storage Settings
MAX_IMAGE_SIZE_MB=10
IMAGE_COMPRESSION_QUALITY=95
```

## 🚀 Installation Steps

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

The following packages were added for image generation:
- `openai>=1.30.0` - OpenAI API client
- `celery[redis]>=5.3.0` - Task queue system
- `redis>=5.0.0` - Redis client
- `pillow>=10.0.0` - Image processing
- `httpx>=0.24.0` - Async HTTP client

### 2. Database Migration

Apply the new database schema for image tables:

```bash
cd backend
python -m alembic upgrade head
```

### 3. Start Required Services

#### Option A: Manual Start
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
cd backend
celery -A src.infrastructure.tasks.celery_app worker --loglevel=info

# Terminal 3: Start Backend Server
cd backend
python scripts/run_dev_server.py

# Terminal 4: Start Frontend
cd frontend
npm run dev
```

#### Option B: Docker Compose (Recommended)
```bash
# Update docker-compose.yml to include Redis and Celery services
docker-compose up -d
```

### 4. Frontend Dependencies

The frontend components use existing dependencies:
- React + Tailwind CSS for UI
- Existing API service pattern
- Material Icons for navigation

## 🧪 Testing the Implementation

### 1. Backend API Testing

Run the comprehensive test script:

```bash
cd backend
python test_image_generation.py
```

This will test:
- User authentication
- Image generation request
- Task status polling
- Gallery retrieval
- Image download
- Chat integration

### 2. Frontend Testing

1. **Navigate to Image Generation**:
   - Login to your dashboard
   - Click "Generate Images" in sidebar
   - Or go to `/images/generate`

2. **Test Chat Integration**:
   - Open any chat thread
   - Type: `/image a beautiful sunset over mountains`
   - Watch real-time generation progress

3. **Test Gallery Management**:
   - Visit `/images/gallery`
   - View generated images
   - Create collections
   - Download images

## 🎨 Usage Examples

### Basic Image Generation
```
Prompt: "A majestic snow-covered mountain peak at sunset"
Size: 1024x1024
Quality: Standard
Style: Vivid
```

### Advanced Prompts
```
Prompt: "A cyberpunk cityscape at night with neon lights reflecting on wet streets, high detail, cinematic composition, photorealistic"
Size: 1792x1024 (landscape)
Quality: HD
Style: Vivid
```

### Chat Integration
```
User: /image a cute golden retriever puppy playing in a garden
Assistant: 🎨 Generating image: "a cute golden retriever puppy playing in a garden"...
[Image appears with metadata]
```

## 📊 Cost Management

### DALL-E 3 Pricing (as of 2024)
- **Standard Quality**: $0.04 per image (1024x1024)
- **HD Quality**: $0.08 per image (1024x1024)
- **Larger sizes**: $0.12 (HD) per 1792x1024 image

### Cost Tracking Features
- Real-time cost calculation
- User spending limits (configurable)
- Monthly usage reports
- Admin cost monitoring

## 🔧 Configuration Options

### Backend Settings (`src/shared/config.py`)

```python
# Image Generation Settings
DALLE_MODEL = "dall-e-3"
DALLE_MAX_RETRIES = 3
DALLE_TIMEOUT_SECONDS = 60
MAX_IMAGES_PER_USER_PER_DAY = 50
MAX_MONTHLY_COST_PER_USER = 10.00  # $10 limit

# Image Storage
MAX_IMAGE_SIZE_MB = 10
IMAGE_COMPRESSION_QUALITY = 95
AUTO_CLEANUP_DAYS = 30  # Delete images after 30 days
```

### Celery Configuration

```python
# Task timeouts
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes

# Retry configuration
CELERY_TASK_RETRY_DELAYS = [1, 2, 4, 8, 16]  # Exponential backoff
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Redis Connection Error
```
Error: Redis connection failed
Solution: Ensure Redis server is running on port 6379
```

#### 2. OpenAI API Error
```
Error: Invalid API key or quota exceeded
Solution: Check OPENAI_API_KEY and billing status
```

#### 3. Celery Worker Not Starting
```
Error: ImportError or module not found
Solution: Ensure all dependencies installed and PYTHONPATH set
```

#### 4. Image Generation Timeout
```
Error: Task timed out after 300 seconds
Solution: Check network connection and OpenAI API status
```

### Debug Commands

```bash
# Check Redis connection
redis-cli ping

# Test Celery worker
celery -A src.infrastructure.tasks.celery_app inspect active

# Monitor task queue
celery -A src.infrastructure.tasks.celery_app flower

# Check database tables
python -c "from src.infrastructure.database.image_models import *; print('Tables exist')"
```

## 📈 Performance Optimization

### 1. Image Caching
- Base64 images stored in PostgreSQL
- Consider file storage for production scale
- Implement CDN for image delivery

### 2. Task Queue Optimization
- Use multiple Celery workers for concurrent generation
- Implement task prioritization
- Monitor queue length and processing time

### 3. Database Optimization
- Index frequently queried fields
- Implement pagination for galleries
- Consider archiving old images

## 🔐 Security Considerations

### 1. Content Filtering
- Implement prompt content filtering
- Monitor for inappropriate image requests
- User reporting system

### 2. Rate Limiting
- API endpoint rate limiting
- Per-user generation limits
- IP-based restrictions

### 3. Data Protection
- Secure API key storage
- Image metadata privacy
- GDPR compliance for image data

## 🚀 Production Deployment

### 1. Environment Setup
```bash
# Production environment variables
export ENVIRONMENT=production
export REDIS_URL=redis://prod-redis:6379/0
export CELERY_BROKER_URL=redis://prod-redis:6379/0
```

### 2. Service Configuration
```yaml
# docker-compose.prod.yml
services:
  redis:
    image: redis:alpine
    restart: always
    
  celery:
    build: .
    command: celery -A src.infrastructure.tasks.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres
```

### 3. Monitoring
- Celery Flower for task monitoring
- Redis monitoring
- Image generation metrics
- Cost tracking alerts

## 📚 API Documentation

### Image Generation Endpoints

```http
POST /images/generate
Content-Type: application/json
Authorization: Bearer <token>

{
  "prompt": "string",
  "size": "1024x1024|1792x1024|1024x1792",
  "quality": "standard|hd",
  "style": "vivid|natural",
  "thread_id": "integer (optional)"
}

Response: 202 Accepted
{
  "task_id": "string",
  "status": "pending",
  "estimated_time": 30
}
```

```http
GET /images/tasks/{task_id}/status
Authorization: Bearer <token>

Response: 200 OK
{
  "status": "completed|pending|failed",
  "progress": 100,
  "image_data": {
    "id": "integer",
    "original_prompt": "string",
    "revised_prompt": "string",
    "size": "string",
    "generation_cost": 0.04,
    "image_data": "base64_string"
  }
}
```

## 🎉 Feature Complete!

The Image Generation feature is now fully implemented with:

✅ **Backend Implementation**
- DALL-E 3 API integration
- Async task processing with Celery
- PostgreSQL storage with proper models
- REST API endpoints
- Chat integration support

✅ **Frontend Implementation**  
- Image generation interface
- Real-time progress tracking
- Gallery management
- Chat integration with `/image` command
- Responsive design

✅ **Production Ready**
- Error handling and retries
- Cost tracking and limits
- Security considerations
- Performance optimization
- Comprehensive testing

The system is ready for deployment and user testing!