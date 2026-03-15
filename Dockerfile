FROM python:3.12-slim

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# System deps: ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Default output directory (override with OUTPUT_DIR env var)
RUN mkdir -p /music && chown -R appuser:appgroup /music /app

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
