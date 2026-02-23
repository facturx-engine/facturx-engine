# =============================================================================
# Factur-X Engine — Multi-stage Dockerfile
#
# Stage 1 (jlink-builder): Downloads VeraPDF via headless IzPack installer
#   from the official distribution server and builds a minimal custom JRE
#   using jlink. The resulting JRE contains only the modules actually needed
#   by VeraPDF (~70-90 MB vs ~200 MB for a full headless JRE).
#
# Stage 2 (runtime): python:3.11-slim + custom JRE + VeraPDF JAR + Python app.
#
# VeraPDF version: update VERAPDF_VERSION to the latest stable release.
# Releases: https://software.verapdf.org/releases/
# =============================================================================

# ----------------------------------------
# Stage 1: Install VeraPDF + build minimal JRE with jlink
# ----------------------------------------
FROM eclipse-temurin:17-jdk-jammy AS jlink-builder

ARG VERAPDF_VERSION=1.26.2
ARG VERAPDF_MAJOR_MINOR=1.26

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Write AutomatedInstallation XML for IzPack headless installer.
# Panel IDs match the VeraPDF Greenfield 1.x installer specification.
RUN printf '%s\n' \
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' \
    '<AutomatedInstallation langpack="eng">' \
    '    <com.izforge.izpack.panels.htmlhello.HTMLHelloPanel id="htmlhello"/>' \
    '    <com.izforge.izpack.panels.target.TargetPanel id="target">' \
    '        <installpath>/opt/verapdf</installpath>' \
    '    </com.izforge.izpack.panels.target.TargetPanel>' \
    '    <com.izforge.izpack.panels.packs.PacksPanel id="packs">' \
    '        <pack index="0" name="veraPDF software" selected="true"/>' \
    '    </com.izforge.izpack.panels.packs.PacksPanel>' \
    '    <com.izforge.izpack.panels.install.InstallPanel id="install"/>' \
    '    <com.izforge.izpack.panels.finish.FinishPanel id="finish"/>' \
    '</AutomatedInstallation>' \
    > /tmp/verapdf-auto-install.xml

# Download the Greenfield installer from the official distribution server
# and perform a fully headless installation to /opt/verapdf
RUN wget -q \
    "https://software.verapdf.org/releases/${VERAPDF_MAJOR_MINOR}/verapdf-greenfield-${VERAPDF_VERSION}-installer.jar" \
    -O /tmp/verapdf-installer.jar && \
    java -jar /tmp/verapdf-installer.jar /tmp/verapdf-auto-install.xml && \
    rm /tmp/verapdf-installer.jar /tmp/verapdf-auto-install.xml

# Locate the installed CLI fat JAR and stage it at /verapdf.jar.
# The IzPack installer places the executable JAR at /opt/verapdf/verapdf-<version>.jar.
# We exclude uninstaller JARs and take the highest version if multiple are found.
RUN JAR=$(find /opt/verapdf -maxdepth 2 -name "verapdf-*.jar" \
        ! -name "*uninstall*" \
        | sort -V | tail -1) && \
    test -n "$JAR" || { echo "ERROR: VeraPDF JAR not found after installation" >&2; exit 1; } && \
    echo "Packaging VeraPDF JAR: $JAR" && \
    cp "$JAR" /verapdf.jar

# Detect required JDK modules via jdeps, then merge with a known-good base set.
# --ignore-missing-deps: tolerates non-modular (automatic module) dependencies
# inside VeraPDF's fat JAR — outputs only JDK module names.
# The hardcoded base set covers modules that jdeps misses due to reflection
# (jdk.unsupported → sun.misc.Unsafe, java.desktop → font metrics).
RUN DETECTED=$(jdeps --ignore-missing-deps --print-module-deps /verapdf.jar \
        2>/dev/null | grep -v '^$' || echo "") && \
    BASE="java.base,java.desktop,java.logging,java.management,java.naming,java.xml,java.xml.crypto,jdk.unsupported" && \
    ALL="${DETECTED:+${DETECTED},}${BASE}" && \
    UNIQUE=$(printf "%s" "$ALL" | tr ',' '\n' | grep -v '^$' | sort -u | tr '\n' ',' | sed 's/,$//') && \
    jlink \
        --no-header-files \
        --no-man-pages \
        --compress=2 \
        --strip-debug \
        --module-path "${JAVA_HOME}/jmods" \
        --add-modules "${UNIQUE}" \
        --output /custom-jre

# ----------------------------------------
# Stage 2: Runtime image
# ----------------------------------------
FROM python:3.11-slim-bookworm

LABEL maintainer="Factur-X Engine"
LABEL description="Self-hosted Factur-X API with EN16931 + PDF/A-3b validation"
LABEL org.opencontainers.image.title="Factur-X Engine"
LABEL org.opencontainers.image.description="The Privacy-First Invoicing Engine (100% Air-gapped)"
LABEL org.opencontainers.image.vendor="Factur-X Engine"
LABEL org.opencontainers.image.version="1.5.5"
LABEL org.opencontainers.image.licenses="FSL-1.1"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Inject the custom JRE and VeraPDF JAR from the builder stage
COPY --from=jlink-builder /custom-jre /opt/jre
COPY --from=jlink-builder /verapdf.jar /app/bin/verapdf.jar

# Make the custom JRE the default java on PATH
ENV PATH="/opt/jre/bin:${PATH}"

# Tell the validation service where to find VeraPDF
ENV VERAPDF_JAR=/app/bin/verapdf.jar

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

# License attribution
COPY LICENSE_SAXON .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check — also validates that the custom JRE is functional
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--max-requests", "1000", "--max-requests-jitter", "50", "--bind", "0.0.0.0:8000", "app.main:app"]
