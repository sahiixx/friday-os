FROM python:3.12-slim

WORKDIR /app

# Install system deps for audio processing and livekit
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

COPY friday-os/pyproject.toml .
COPY friday-os/friday/ ./friday/
COPY friday-os/README.md .
COPY sahiixx-titans-memory /tmp/titans-memory

# Fix local path dependency to work inside container
RUN sed -i 's|file:///home/sahiix/sahiixx-titans-memory|file:///tmp/titans-memory|g' pyproject.toml

# Install with all extras for full functionality
RUN pip install --no-cache-dir -e ".[dev,a2a,voice,memory]"

EXPOSE 8000

ENV FRIDAY_HOST=0.0.0.0
ENV FRIDAY_PORT=8000

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-c", "from friday.core.a2a.server import serve; serve(host='0.0.0.0', port=8000)"]
