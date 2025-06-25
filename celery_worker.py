#!/usr/bin/env python3
"""
Celery worker script for ParsePod
Run this script to start the Celery worker for background task processing.
"""

import os
import sys
from pathlib import Path

# Set development environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the Celery app and tasks from the Flask application
from src.app import celery, process_paper_async

# Ensure the task is registered
celery.autodiscover_tasks(['src.app'])

if __name__ == '__main__':
    # Start the Celery worker
    celery.worker_main(['worker', '--loglevel=info']) 