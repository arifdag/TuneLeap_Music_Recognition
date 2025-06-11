#!/bin/bash

# This script runs the Gunicorn server and the Celery worker.

# Exit immediately if a command exits with a non-zero status.
set -e


# Start the Celery worker in the background.
echo "Starting Celery worker in the background..."
celery -A worker.tasks.celery_app worker --loglevel=info &

# Start the Gunicorn web server in the foreground.
# It will use the WEB_CONCURRENCY variable from the .env file.
echo "Starting Gunicorn server..."
exec gunicorn -k uvicorn.workers.UvicornWorker -w "${WEB_CONCURRENCY:-4}" -b "0.0.0.0:${PORT}" --log-level "${LOG_LEVEL:-info}" api.main:app