ARG REGISTRY=""
FROM ${REGISTRY}python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the worker code
COPY . .

# Run the ARQ listener directly
CMD ["arq", "worker.WorkerSettings"]