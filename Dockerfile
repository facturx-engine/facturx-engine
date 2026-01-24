# Stage 1: Base (Dependencies)
# ==========================================
FROM python:3.11-slim-bookworm AS base
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# Install runtime deps in base to be shared
# We install build-essential temporarily to compile wheels (like lxml/psutil) if pre-built ones miss
RUN apt-get update && apt-get install -y --no-install-recommends build-essential python3-dev && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential python3-dev && \
    rm -rf /var/lib/apt/lists/*

# ==========================================
# Stage 2: Builder (Compile Pro / Cython)
# 🛑 DEV WARNING: THIS STAGE REQUIRES LOCAL-ONLY FILES.
# DO NOT ATTEMPT TO RUN THIS ON GITHUB ACTIONS.
# ==========================================
FROM python:3.11-slim-bookworm AS builder-pro
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir cython wheel setuptools && pip install --no-cache-dir -r requirements.txt
COPY app/ app/
COPY setup.py .
# Build Date Injection (Fail Fast)
ARG BUILD_DATE=2024-01-01
RUN echo "$BUILD_DATE" | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' || (echo "Invalid BUILD_DATE format" && exit 1) && \
    sed -i "s/BUILD_DATE_PLACEHOLDER/$BUILD_DATE/g" /app/app/license.py && \
    rm -rf build && \
    python setup.py build_ext --inplace --verbose && \
    python -c "import app.license as m; print(f'VERIFICATION: BUILD_DATE={m.BUILD_DATE}'); assert m.BUILD_DATE == '$BUILD_DATE', f'FAILED: {m.BUILD_DATE}'" && \
    rm /app/app/license.py
RUN rm -f app/license.py app/services/extractor.py app/services/generator.py app/services/validator.py
RUN rm -f app/services/*.c app/*.c
# Verify
RUN find app -name "*.so" -type f | grep -q . || exit 1

# ==========================================
# Stage 3: Runtime Unified (Pro + Community)
# ==========================================
FROM base AS final
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=builder-pro /app/app /app/app

# Inject Demo Extractor as fallback
COPY community_stubs/app/services/extractor.py /app/app/services/extractor_demo.py

# Copy installed packages from builder (Cython modules dependencies)
COPY --from=builder-pro /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
WORKDIR /app
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
