# STAGE 1: Build 
FROM python:3.14-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Added rust and cargo: required to compile python-jose[cryptography] and bcrypt on Alpine
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    python3-dev \
    libffi-dev \
    cargo \
    rust

WORKDIR /app

# Install dependencies into a separate directory
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# STAGE 2: Base Runtime
FROM python:3.14-alpine AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Keeping libpq for potential PostgreSQL database usage
RUN apk add --no-cache libpq

WORKDIR /app

# Copy the pre-compiled libraries from the builder stage
COPY --from=builder /install /usr/local

# STAGE 3: Development
FROM base AS dev
COPY . .
EXPOSE 5000
# Updated entrypoint: main.py is now at the root directory, not inside the app/ folder
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]

# STAGE 4: Production
FROM base AS prod
COPY . .
EXPOSE 5000
# Updated entrypoint: main.py is now at the root directory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]