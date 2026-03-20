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

ARG VERAPDF_VERSION=1.28.2
ARG VERAPDF_MAJOR_MINOR=1.28

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates unzip && \
    rm -rf /var/lib/apt/lists/*

# Write AutomatedInstallation XML for IzPack headless installer.
# Panel IDs are extracted from resources/panelsOrder inside the installer JAR.
# Pack names are extracted from resources/packs.info (ZIP listing: pack-<name>).
RUN printf '%s\n' \
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' \
    '<AutomatedInstallation langpack="eng">' \
    '    <com.izforge.izpack.panels.htmlhello.HTMLHelloPanel id="welcome"/>' \
    '    <com.izforge.izpack.panels.target.TargetPanel id="install_dir">' \
    '        <installpath>/opt/verapdf</installpath>' \
    '    </com.izforge.izpack.panels.target.TargetPanel>' \
    '    <com.izforge.izpack.panels.packs.PacksPanel id="sdk_pack_select">' \
    '        <pack name="veraPDF GUI" selected="true"/>' \
    '        <pack name="veraPDF Validation model" selected="true"/>' \
    '        <pack name="veraPDF Mac and *nix Scripts" selected="true"/>' \
    '        <pack name="veraPDF Batch files" selected="false"/>' \
    '        <pack name="veraPDF Documentation" selected="false"/>' \
    '        <pack name="veraPDF Sample Plugins" selected="false"/>' \
    '    </com.izforge.izpack.panels.packs.PacksPanel>' \
    '    <com.izforge.izpack.panels.install.InstallPanel id="install"/>' \
    '    <com.izforge.izpack.panels.finish.FinishPanel id="finish"/>' \
    '</AutomatedInstallation>' \
    > /tmp/verapdf-auto-install.xml

# Download the Greenfield installer ZIP from the official distribution server.
# The ZIP contains the IzPack installer JAR at:
#   verapdf-greenfield-VERSION/verapdf-izpack-installer-VERSION.jar
RUN wget -q \
    "https://software.verapdf.org/releases/${VERAPDF_MAJOR_MINOR}/verapdf-greenfield-${VERAPDF_VERSION}-installer.zip" \
    -O /tmp/verapdf-installer.zip && \
    if [ -n "$VERAPDF_INSTALLER_SHA256" ]; then \
    echo "${VERAPDF_INSTALLER_SHA256}  /tmp/verapdf-installer.zip" | sha256sum -c - || \
    { echo "ERROR: VeraPDF installer SHA-256 mismatch — possible supply-chain attack!" >&2; exit 1; }; \
    fi && \
    unzip -q /tmp/verapdf-installer.zip -d /tmp/verapdf-installer-dir && \
    java -jar "/tmp/verapdf-installer-dir/verapdf-greenfield-${VERAPDF_VERSION}/verapdf-izpack-installer-${VERAPDF_VERSION}.jar" \
    /tmp/verapdf-auto-install.xml && \
    rm -rf /tmp/verapdf-installer.zip /tmp/verapdf-installer-dir /tmp/verapdf-auto-install.xml

# Supply-chain integrity: expected SHA-256 digests.
# Set these ARGs in CI (--build-arg) to enforce checksum verification.
# Leave empty to skip verification (development / first-time bootstrap only).
# Obtain the correct values with:
#   sha256sum verapdf-greenfield-<VERSION>-installer.zip
#   sha256sum Saxon-HE-<VERSION>.jar
ARG VERAPDF_INSTALLER_SHA256=""
ARG SAXON_JAR_SHA256=""

# Download Saxon-HE 10.8 JAR from Maven Central (10.8 natively includes xmlresolver;
# Saxon 12.x requires a separate xmlresolver JAR — not worth the complexity for XSLT 2.0)
RUN wget -q "https://repo1.maven.org/maven2/net/sf/saxon/Saxon-HE/10.8/Saxon-HE-10.8.jar" -O /saxon.jar && \
    if [ -n "$SAXON_JAR_SHA256" ]; then \
    echo "${SAXON_JAR_SHA256}  /saxon.jar" | sha256sum -c - || \
    { echo "ERROR: Saxon JAR SHA-256 mismatch — possible supply-chain attack!" >&2; exit 1; }; \
    fi

# Locate the installed CLI fat JAR and stage it at /verapdf.jar.
# The IzPack installer places the executable JAR in /opt/verapdf/bin/ as
# greenfield-apps-<version>.jar (not verapdf-*.jar).
RUN JAR=$(find /opt/verapdf/bin -maxdepth 1 -name "greenfield-apps-*.jar" \
    | sort -V | tail -1) && \
    test -n "$JAR" || { echo "ERROR: VeraPDF JAR not found after installation" >&2; exit 1; } && \
    echo "Packaging VeraPDF JAR: $JAR" && \
    cp "$JAR" /verapdf.jar

# Detect required JDK modules via jdeps, then merge with a known-good base set.
# --ignore-missing-deps: tolerates non-modular (automatic module) dependencies
# inside VeraPDF and Saxon fat JARs — outputs only JDK module names.
# The hardcoded base set covers modules that jdeps misses due to reflection
# (jdk.unsupported → sun.misc.Unsafe, java.desktop → font metrics).
RUN DETECTED_VERA=$(jdeps --ignore-missing-deps --print-module-deps /verapdf.jar \
    2>/dev/null | grep -v '^$' || echo "") && \
    DETECTED_SAXON=$(jdeps --ignore-missing-deps --print-module-deps /saxon.jar \
    2>/dev/null | grep -v '^$' || echo "") && \
    BASE="java.base,java.desktop,java.logging,java.management,java.naming,java.xml,java.xml.crypto,jdk.unsupported" && \
    ALL="${DETECTED_VERA:+${DETECTED_VERA},}${DETECTED_SAXON:+${DETECTED_SAXON},}${BASE}" && \
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
LABEL org.opencontainers.image.version="latest"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Inject the custom JRE, VeraPDF JAR, and Saxon JAR from the builder stage
COPY --from=jlink-builder /custom-jre /opt/jre
COPY --from=jlink-builder /verapdf.jar /app/bin/verapdf.jar
COPY --from=jlink-builder /saxon.jar /app/bin/saxon.jar

# Make the custom JRE the default java on PATH
ENV PATH="/opt/jre/bin:${PATH}"

# Tell the validation service where to find VeraPDF and Saxon
ENV VERAPDF_JAR=/app/bin/verapdf.jar
ENV SAXON_JAR=/app/bin/saxon.jar

# Install system dependencies for lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "wheel>=0.46.2" "jaraco.context>=6.1.0"

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

# WORKERS: number of Gunicorn worker processes (default: 4).
# Override at runtime: docker run -e WORKERS=8 ...
# Rule of thumb: 2 × CPU cores + 1 for CPU-bound workloads.
CMD ["sh", "-c", "exec gunicorn -w ${WORKERS:-4} -k uvicorn.workers.UvicornWorker --max-requests 1000 --max-requests-jitter 50 --bind 0.0.0.0:8000 app.main:app"]
