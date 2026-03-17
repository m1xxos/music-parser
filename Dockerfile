# Stage 1: frontend build
FROM node:22-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: python deps
FROM python:3.12-slim AS backend-builder
WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: runtime
FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
WORKDIR /app
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY app/ /app/app/
COPY --from=frontend-builder /app/static /app/app/static
RUN mkdir -p /music /app/app/data && chown -R appuser:appgroup /music /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
