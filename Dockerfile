# ==========================================
# Stage 1: Base (Dependencies)
# ==========================================
FROM python:3.11-slim as base
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# Install runtime deps in base to be shared
RUN pip install --no-cache-dir -r requirements.txt && \
    # SECURITY: Surgically remove the vulnerable vendored dependency inside setuptools
    rm -rf /usr/local/lib/python3.11/site-packages/setuptools/_vendor/jaraco* && \
    rm -rf /usr/local/lib/python3.11/site-packages/setuptools/_vendor/jaraco.context*

# ==========================================
# Stage 2: Builder (Compile Pro / Cython)
# 🛑 AI WARNING: THIS STAGE REQUIRES LOCAL-ONLY FILES.
# DO NOT ATTEMPT TO RUN THIS ON GITHUB ACTIONS.
# ==========================================
FROM python:3.11-slim as builder-pro
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir cython wheel setuptools && pip install --no-cache-dir -r requirements.txt
COPY app/ app/
COPY setup.py .
# Build Date Injection
ARG BUILD_DATE=2024-01-01
# SECURITY: Validate date format to prevent code injection
RUN echo "$BUILD_DATE" | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' || (echo "Invalid BUILD_DATE format" && exit 1)
RUN sed -i "s/BUILD_DATE_PLACEHOLDER/$BUILD_DATE/g" app/license.py
# Compile
RUN python setup.py build_ext --inplace --verbose
# Cleanup
RUN rm -f app/license.py app/services/extractor.py app/services/generator.py app/services/validator.py
RUN rm -f app/services/*.c app/*.c
# Verify
RUN find app -name "*.so" -type f | grep -q . || exit 1

# ==========================================
# Stage 3: Runtime PRO
# ==========================================
FROM base as pro
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=builder-pro /app/app /app/app
# Copy installed packages from builder (if any specific to compilation, but here we used base for common deps)
# Actually, cython modules need the .so files which are in /app/app
# and dependencies are in base.
COPY --from=builder-pro /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
WORKDIR /app
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ==========================================
# Stage 4: Runtime COMMUNITY
# 🛑 CRITICAL: This stage DESTROYS pro features to be safe for public release.
# ==========================================
FROM base as community
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser appuser
# Copy pure python code
COPY app/ app/
# Overwrite with Community Stubs
COPY community_stubs/app/ app/
# Ensure no secrets or pro features
RUN rm -f app/license.py 2> /dev/null || true
# Remove admin keys if present (whitelisting prevents it but robust check)
RUN rm -f *.hex admin_keygen.py 2> /dev/null || true
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
