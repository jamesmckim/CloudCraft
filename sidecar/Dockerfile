# 
ARG REGISTRY=""
FROM ${REGISTRY}python:3.14.1-alpine3.23

WORKDIR /app

# We rely solely on the Python Standard Library.
# No pip install needed. No system packages needed.

COPY . .

# Default environment variables
ENV TICK_RATE=30 \
    IDLE_THRESHOLD=900 \
    GAME_TYPE=generic

# Using -u for unbuffered output is crucial for container logs
CMD ["python", "-u", "main.py"]