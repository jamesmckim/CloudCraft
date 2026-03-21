ARG REGISTRY=""
FROM ${REGISTRY}python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper.py .
RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "scraper.py"]
