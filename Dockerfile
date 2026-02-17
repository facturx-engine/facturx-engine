# ==========================================
# Factur-X Engine - Simplified Dockerfile
# Single-stage, no Cython, pure Python
# ==========================================
FROM python:3.11-slim-bookworm

LABEL maintainer="Factur-X Engine"
LABEL description="Self-hosted Factur-X API with EN16931 validation"
LABEL org.opencontainers.image.title="Factur-X Engine"
LABEL org.opencontainers.image.description="The Privacy-First Invoicing Engine (100% Air-gapped)"
LABEL org.opencontainers.image.vendor="Factur-X Engine"
LABEL org.opencontainers.image.version="1.4.5"
LABEL org.opencontainers.image.licenses="FSL-1.1"

WORKDIR /app

# Install system dependencies for lxml/saxonc
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Application code includes hybrid_validation_service.py

# License attribution
COPY LICENSE_SAXON .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--max-requests", "1000", "--max-requests-jitter", "50", "--bind", "0.0.0.0:8000", "app.main:app"]
