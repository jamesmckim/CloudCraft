# STAGE 1: Build
ARG REGISTRY=""
FROM ${REGISTRY}python:3.14-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Install build dependencies for C-extensions
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    python3-dev \
    libffi-dev

WORKDIR /app

COPY requirements.txt .
# Install dependencies into a separate directory for easy copying
RUN pip install --prefix=/install -r requirements.txt

# STAGE 2: Base Runtime
FROM ${REGISTRY}python:3.14-alpine AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install only the runtime library for postgres
RUN apk add --no-cache libpq

WORKDIR /app

# Copy the pre-compiled libraries from the builder stage
COPY --from=builder /install /usr/local

# STAGE 3: Development
FROM base AS dev
COPY . .
EXPOSE 5000
# Development uses --reload for hot-swapping code
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]

# STAGE 4: Production
FROM base AS prod
COPY . .
EXPOSE 5000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]