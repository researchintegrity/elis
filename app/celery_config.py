"""
Celery configuration for async task processing
"""
from celery import Celery
import os
from datetime import timedelta

# Redis connection settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB + 1}"

# Create Celery app
celery_app = Celery(
    "elis_tasks",
    broker=broker_url,
    backend=result_backend
)

# Configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    task_acks_late=True,  # Acknowledge after task completes
    
    # Retry settings
    task_max_retries=3,
    task_default_retry_delay=60,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
        "retry_on_timeout": True,
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)
