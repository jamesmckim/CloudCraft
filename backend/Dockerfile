# STAGE 1: Build
FROM python:3.14-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

RUN apk add --no-cache \
    gcc \
    musl-dev \
	postgresql-dev \
    python3-dev \
    libffi-dev

WORKDIR /app

# Install dependencies into a separate directory
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# STAGE 2
FROM python:3.14-alpine

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apk add --no-cache libpq

WORKDIR /app

# Copy the pre-compiled libraries from the builder stage
COPY --from=builder /install /usr/local

COPY . .

EXPOSE 5000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]