"""
Celery Configuration for Async Task Processing

Provides Redis-backed task queue for image generation and other async operations.
"""
from celery import Celery
from ...shared.config import get_settings

settings = get_settings()

# Create Celery app instance
celery_app = Celery(
    "user_auth_tasks",
    broker=settings.redis_url or "redis://localhost:6379/0",
    backend=settings.redis_url or "redis://localhost:6379/0",
    include=[
        'src.infrastructure.tasks.image_tasks',
        # Add other task modules here as needed
    ]
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'image_generation.*': {'queue': 'image_generation'},
        'default': {'queue': 'default'},
    },
    
    # Task execution
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Task retries
    task_default_retry_delay=60,  # 60 seconds
    task_max_retries=3,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Force import of tasks to ensure they're registered
try:
    from . import image_tasks
    print("✅ Successfully imported image_tasks module")
except ImportError as e:
    print(f"❌ Failed to import image_tasks: {e}")

# Optional: Configure beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-expired-tasks': {
        'task': 'image_generation.cleanup_expired_tasks',
        'schedule': 3600.0,  # Run every hour
    },
}