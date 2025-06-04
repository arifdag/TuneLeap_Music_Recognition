#!/bin/bash

# Set default values if environment variables are not set
HOST=${APP_HOST:-0.0.0.0}
PORT=${APP_PORT:-8000}
LOG_LEVEL=${LOG_LEVEL:-info}
WORKERS=${WEB_CONCURRENCY:-4} # Number of Gunicorn workers

# Start Gunicorn with Uvicorn workers
exec gunicorn -k uvicorn.workers.UvicornWorker -w $WORKERS -b $HOST:$PORT --log-level $LOG_LEVEL api.main:app