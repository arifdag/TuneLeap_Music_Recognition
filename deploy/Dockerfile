FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set default environment variables for the application
ENV WEB_CONCURRENCY=4
ENV PORT=8000
ENV LOG_LEVEL=info

# Install system dependencies that might be needed by Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make the run.sh script executable
RUN chmod +x run.sh

# Expose the port that Gunicorn will run on
EXPOSE 8000

# The command to run the application
CMD ["./run.sh"]