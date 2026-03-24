# backend/Dockerfile.worker
ARG REGISTRY=""
FROM ${REGISTRY}python:3.14-slim

# Prevent Python from writing .pyc files and keep stdout unbuffered for real-time logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the worker requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Start the ARQ worker process
CMD ["arq", "ai_worker.WorkerSettings"]