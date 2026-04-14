FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/music-parser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data/music /data/tmp \
    && chown -R appuser:appuser /opt/music-parser /data

USER appuser

ENV OUTPUT_ROOT=/data/music \
    TMP_ROOT=/data/tmp \
    DEFAULT_AUDIO_FORMAT=mp3 \
    DEFAULT_AUDIO_QUALITY=320

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
