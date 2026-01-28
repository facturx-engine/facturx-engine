# ==========================================
# Factur-X Engine - Simplified Dockerfile
# Single-stage, no Cython, pure Python
# ==========================================
FROM python:3.11-slim-bookworm

LABEL maintainer="Factur-X Engine"
LABEL description="Self-hosted Factur-X API with EN16931 validation"

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

# Copy Hybrid Validator from prototype
COPY prototypes/saxonc_validation/hybrid_validator.py prototypes/saxonc_validation/hybrid_validator.py

# Copy EN16931 Schematron XSLT rules (official EU validation)
COPY docs/2025_12_04_FNFE_SCHEMATRONS_FR_CTC_V1.2.0/_EN16931_Schematrons_V1.3.15_CII_ET_UBL/_XSLT/ docs/2025_12_04_FNFE_SCHEMATRONS_FR_CTC_V1.2.0/_EN16931_Schematrons_V1.3.15_CII_ET_UBL/_XSLT/

# Copy XSD schemas
COPY docs/2025_12_04_FNFE_SCHEMATRONS_FR_CTC_V1.2.0/_CII_D22B_XSD/ docs/2025_12_04_FNFE_SCHEMATRONS_FR_CTC_V1.2.0/_CII_D22B_XSD/

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

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
