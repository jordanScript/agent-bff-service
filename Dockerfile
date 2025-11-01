# FastAPI on Cloud Run
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# Cloud Run listens on $PORT; default to 8080
ENV PORT=8080
ENV SERVICE_NAME=fastapi-service

EXPOSE 8080

# Start server
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
