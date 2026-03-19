"""
Factur-X API - Main Application Entry Point
"""
import logging
import multiprocessing
import os
import subprocess

# For Windows multiprocessing support (spawn)
if os.name == 'nt':
    multiprocessing.freeze_support()

# Configure logging
import json
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.diagnostics import router as diagnostics_router


# Structured JSON Logging for Industrial Grade Observability
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        # Add extra context if present
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)

# Configure Log Handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)

logger = logging.getLogger(__name__)

from fastapi.responses import RedirectResponse

from app.constants import PRODUCT_NAME
from app.version import __version__

# OpenAPI tag grouping — controls Swagger UI and doc generators
tags_metadata = [
    {
        "name": "Core Workflows",
        "description": "The four primary e-invoicing operations: validate, generate XML, merge PDF+XML, and extract data from received invoices.",
    },
    {
        "name": "Advanced Integration",
        "description": "ERP serialization (Pro) and convenience conversion shortcuts for advanced integrations.",
    },
    {
        "name": "Operations",
        "description": "Health probes, readiness checks, diagnostics, and Prometheus metrics.",
    },
]

# Create FastAPI application
app = FastAPI(
    title=PRODUCT_NAME,
    description="Production-ready REST API for Factur-X (ZUGFeRD 2.4) conversions and data extraction.",
    version=__version__,
    openapi_tags=tags_metadata,
)

# Include Routers
app.include_router(router)
app.include_router(diagnostics_router)


from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.errors import ProblemDetails


def _sanitize_validation_errors(errors: list) -> list:
    """
    Sanitize FastAPI validation error dicts before JSON serialisation.

    FastAPI includes the raw input value in each error dict.  When the input
    is an UploadFile object (multipart/form-data endpoint), that object is not
    JSON-serialisable and causes a secondary TypeError → HTTP 500.  Replace
    any non-primitive input value with a safe string representation.
    """
    sanitized = []
    for err in errors:
        safe_err = dict(err)
        raw_input = safe_err.get("input")
        if raw_input is not None and not isinstance(raw_input, (str, int, float, bool, list, dict, type(None))):
            # UploadFile, SpooledTemporaryFile, or any other non-primitive
            filename = getattr(raw_input, "filename", None)
            safe_err["input"] = f"<UploadFile: {filename}>" if filename else f"<{type(raw_input).__name__}>"
        sanitized.append(safe_err)
    return sanitized


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Format standard FastAPI validation errors (e.g., missing fields, bad types) into RFC 9457 format.
    """
    errors = _sanitize_validation_errors(exc.errors())
    # Simple formatting of the first validation error
    detail_msg = ", ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors])

    problem = ProblemDetails(
        type="about:blank",
        title="Bad Request",
        status=400,
        detail=f"Validation failed: {detail_msg}",
        instance=str(request.url.path),
        extensions={"errors": errors}
    )
    return JSONResponse(status_code=400, content=problem.model_dump(exclude_none=True))

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Format standard HTTPExceptions into RFC 9457 format.
    """
    # If the detail is already a dict (our old error format), extract message and error code
    detail_str = str(exc.detail)
    error_code = "urn:facturx:error:api"
    
    if isinstance(exc.detail, dict):
        detail_str = exc.detail.get("message", detail_str)
        error_code = f"urn:facturx:error:{exc.detail.get('error', '').lower()}" or error_code
        
    problem = ProblemDetails(
        type=error_code,
        title="API Error",
        status=exc.status_code,
        detail=detail_str,
        instance=str(request.url.path)
    )
    return JSONResponse(status_code=exc.status_code, content=problem.model_dump(exclude_none=True))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Format unhandled exceptions into RFC 9457 format.
    """
    logger.exception(f"Unhandled Global Exception: {exc}")
    problem = ProblemDetails(
        type="urn:facturx:error:internal",
        title="Internal Server Error",
        status=500,
        detail="An unexpected error occurred processing the request.",
        instance=str(request.url.path)
    )
    return JSONResponse(status_code=500, content=problem.model_dump(exclude_none=True))

# Switch to on_event which is more robust for logging in some versions
@app.on_event("startup")
async def startup_event():
    # STARTUP: Validating Environment
    logger.info(f"Initializing {PRODUCT_NAME}...")
    
    # 1. INTEGRITY CHECK: Critical Schemas
    # Use absolute path relative to this file to be robust against CWD changes
    base_dir = Path(__file__).parent
    schema_path = base_dir / "resources" / "schemas" / "Factur-X_1.08_EN16931.xsd"
    
    if not schema_path.exists():
        logger.critical(f"🚨 FATAL: Validation schema missing at {schema_path}")
        logger.critical("   The application cannot start without EN16931 schemas.")
        sys.exit(1)
    logger.info("✅ Schema integrity verified (Factur-X 1.08).")

    # 2. VERAPDF & SAXON CHECK: Verify custom JRE + JARs are accessible
    verapdf_jar = os.getenv("VERAPDF_JAR", "")
    saxon_jar = os.getenv("SAXON_JAR", "")
    
    # Check JRE functionality if either is configured
    if verapdf_jar or saxon_jar:
        try:
            result = subprocess.run(["java", "-version"], capture_output=True, timeout=10)
            if result.returncode == 0:
                logger.info("✅ Java JRE ready (functional).")
            else:
                logger.warning(f"⚠️  Java JRE check failed (exit {result.returncode}). Subprocess validation may not work.")
        except FileNotFoundError:
            logger.warning("⚠️  'java' not found in PATH. Subprocess validation disabled.")
        except subprocess.TimeoutExpired:
            logger.warning("⚠️  JRE check timed out at startup. Continuing anyway.")
            
    if verapdf_jar:
        if not Path(verapdf_jar).exists():
            logger.warning(f"⚠️  VERAPDF_JAR configured but JAR not found: {verapdf_jar}")
            logger.warning("   PDF/A-3b validation will be skipped until the JAR is available.")
        else:
            logger.info("✅ VeraPDF JAR present.")
    else:
        logger.info("ℹ️  VERAPDF_JAR not set — PDF/A-3b validation disabled.")
        
    if saxon_jar:
        if not Path(saxon_jar).exists():
            logger.warning(f"⚠️  SAXON_JAR configured but JAR not found: {saxon_jar}")
            logger.warning("   Schematron validation will fail until the JAR is available.")
        else:
            logger.info("✅ Saxon-HE JAR present.")
    else:
        logger.info("ℹ️  SAXON_JAR not set — Defaulting to skip Schematron evaluation.")

    # LICENSE CHECK: Fail Fast Strategy
    try:
        # Try to import licensing module (Only in Pro)
        from app.license import is_licensed
        
        license_key = os.getenv("LICENSE_KEY", "").strip()
        
        if license_key:
            # User explicitly requested Pro Mode
            logger.info("Verifying License Key integrity...")
            if not is_licensed():
                logger.critical("🚨 FATAL CONFIGURATION ERROR: The provided LICENSE_KEY is INVALID.")
                logger.critical("   The application is refusing to start to prevent accidental fallback to Demo Mode.")
                sys.exit(1) # Crash container immediately
            else:
                logger.info("✅ PRO LICENSE VERIFIED. Full Engine Capabilities Unlocked.")
        else:
            logger.warning("ℹ️ No LICENSE_KEY found. Engine running in Community Mode.")
            
    except ImportError:
        # Community Edition
        logger.info("ℹ️ Factur-X Community Edition Active.")
    except Exception as e:
        logger.critical(f"CRITICAL STARTUP ERROR: {e}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down API...")

from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send


# SECURITY: DoS Protection via Max Upload Size
class LimitUploadSize:
    """
    Pure ASGI middleware enforcing a maximum request body size.

    Two-layer defence:
    1. Fast-path: reject immediately when Content-Length header exceeds the limit
       (no body read required).
    2. Streaming fallback: buffer the body chunk-by-chunk from the ASGI `receive`
       callable and abort once the accumulated size exceeds the limit.  This covers
       chunked transfer encoding (Transfer-Encoding: chunked) where no Content-Length
       header is sent.

    Unlike BaseHTTPMiddleware, this pure ASGI implementation wraps the `receive`
    callable directly so that downstream handlers (FastAPI form parsers, UploadFile)
    can still read the cached body after the size check passes.
    """

    def __init__(self, app: ASGIApp, max_upload_size: int) -> None:
        self.app = app
        self.max_upload_size = max_upload_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in ("POST", "PUT", "PATCH"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))

        # Layer 1 — Content-Length fast-path (no body buffering needed)
        raw_cl = headers.get(b"content-length")
        if raw_cl is not None:
            try:
                content_length = int(raw_cl)
                if content_length > self.max_upload_size:
                    logger.warning(
                        f"Blocked upload (Content-Length): {content_length} bytes "
                        f"> limit {self.max_upload_size} bytes"
                    )
                    response = Response(
                        f"File too large. Maximum allowed size is "
                        f"{self.max_upload_size // (1024 * 1024)} MB.",
                        status_code=413,
                    )
                    await response(scope, receive, send)
                    return
            except ValueError:
                pass  # Malformed Content-Length — fall through to Layer 2

        # Layer 2 — Buffer body and check size (handles chunked / no Content-Length)
        chunks: list[bytes] = []
        received = 0
        more_body = True

        while more_body:
            message = await receive()
            body_chunk = message.get("body", b"")
            received += len(body_chunk)

            if received > self.max_upload_size:
                logger.warning(
                    f"Blocked upload (streaming): received {received} bytes "
                    f"> limit {self.max_upload_size} bytes"
                )
                response = Response(
                    f"File too large. Maximum allowed size is "
                    f"{self.max_upload_size // (1024 * 1024)} MB.",
                    status_code=413,
                )
                await response(scope, receive, send)
                return

            chunks.append(body_chunk)
            more_body = message.get("more_body", False)

        cached_body = b"".join(chunks)

        # Wrap receive so downstream ASGI apps read the cached body, not the
        # already-exhausted original stream.
        body_sent = False

        async def cached_receive() -> dict:
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": cached_body, "more_body": False}
            # After body is delivered, forward any subsequent messages (e.g. disconnect)
            return await receive()

        await self.app(scope, cached_receive, send)

# Configure Middlewares
# 1. Size Limit (First line of defense)
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", 10))
app.add_middleware(LimitUploadSize, max_upload_size=MAX_UPLOAD_SIZE_MB * 1024 * 1024) 

# 2. Configure CORS (Secure by Default)
# CORS_ORIGINS must be an explicit comma-separated list of allowed origins.
# Defaulting to "*" (wildcard) combined with allow_credentials=True violates the
# CORS specification (RFC 6454 / Fetch Spec) and is rejected by all modern browsers.
# In self-hosted / air-gapped deployments the default is an empty list (no CORS),
# which is safe. Set CORS_ORIGINS explicitly when a browser-based UI needs access.
cors_env = os.getenv("CORS_ORIGINS", "").strip()
if cors_env:
    allow_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
else:
    allow_origins = []  # No cross-origin requests allowed by default

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=bool(allow_origins),  # credentials only when origins are explicit
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers



@app.get("/", include_in_schema=False)
async def root():
    """
    Redirects to API Documentation.
    """
    return RedirectResponse(url="/docs")



@app.get("/health", tags=["Operations"])
async def health_check():
    """
    Liveness probe (Kubernetes).

    Returns 200 OK immediately if the HTTP server is responsive.
    This endpoint is intentionally lightweight — no subprocess calls,
    no disk I/O — so it can be polled frequently without overhead.

    Use `/healthz` for a deeper readiness check.
    """
    return {
        "status": "healthy",
        "service": "factur-x-api",
        "version": __version__,
    }


@app.get("/license/status", tags=["Operations"])
async def license_status():
    """
    Lightweight license introspection (no secrets exposed).

    Returns the current licensing mode, tier, and expiry so operators
    can verify that a key was accepted without calling a Pro endpoint.
    """
    from app.license import get_license_payload

    payload = get_license_payload()
    if payload is None:
        return {
            "mode": "community",
            "valid": False,
            "tier": None,
            "expires_at": None,
        }

    return {
        "mode": "paid",
        "valid": True,
        "tier": payload.get("tier"),
        "expires_at": payload.get("exp"),
    }


@app.get("/healthz", tags=["Operations"])
async def readiness_check():
    """
    Readiness probe (Kubernetes).

    Returns the status of each critical subsystem:
    - API process (always healthy if this responds)
    - VeraPDF / Saxon / custom JRE (present and executable)
    """
    verapdf_jar = os.getenv("VERAPDF_JAR", "")
    saxon_jar = os.getenv("SAXON_JAR", "")

    def check_jar(jar_path: str) -> dict:
        if not jar_path:
            return {"status": "not_configured"}
        if not os.path.exists(jar_path):
            return {"status": "jar_missing", "jar": jar_path}

        try:
            proc = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                timeout=5,
            )
            if proc.returncode == 0:
                return {"status": "available", "jar": jar_path}
            else:
                return {
                    "status": "jre_error",
                    "jar": jar_path,
                    "detail": proc.stderr.decode(errors="replace")[:200],
                }
        except FileNotFoundError:
            return {"status": "java_not_found"}
        except subprocess.TimeoutExpired:
            return {"status": "jre_timeout"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    verapdf_status = check_jar(verapdf_jar)
    saxon_status = check_jar(saxon_jar)
    dependency_statuses = [verapdf_status.get("status"), saxon_status.get("status")]
    has_hard_failure = any(s not in ("available", "not_configured") for s in dependency_statuses)
    has_config_gap = any(s == "not_configured" for s in dependency_statuses)

    if has_hard_failure:
        overall = "degraded"
        status_code = 503
    elif has_config_gap:
        overall = "degraded"
        status_code = 200
    else:
        overall = "healthy"
        status_code = 200

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "service": "factur-x-api",
            "version": __version__,
            "verapdf": verapdf_status,
            "saxon": saxon_status,
        },
    )

@app.get("/metrics", tags=["Operations"], include_in_schema=True)
async def metrics_endpoint(request: Request):
    """
    Prometheus-compatible metrics endpoint.
    
    Security:
    - Community Edition: Disabled (HTTP 403).
    - Pro Edition: Disabled by default. Requires METRICS_ENABLED=true and METRICS_TOKEN=<secret>.
    """
    import os

    from fastapi.responses import JSONResponse, PlainTextResponse

    from app.license import is_licensed
    from app.metrics import metrics
    
    is_pro = os.getenv("LICENSE_KEY") and is_licensed()
    
    if not is_pro:
        # Community Mode: Metrics disabled with upsell message
        return JSONResponse(
            status_code=403,
            content={
                "error": "PRO_FEATURE_REQUIRED",
                "message": "Prometheus metrics integration is a Pro feature. Get your evaluation key at https://facturx-engine.lemonsqueezy.com"
            }
        )
        
    # Pro Mode: Check if explicitly enabled
    metrics_enabled = os.getenv("METRICS_ENABLED", "false").lower() == "true"
    if not metrics_enabled:
        return JSONResponse(
            status_code=404,
            content={"error": "NOT_FOUND", "message": "Metrics endpoint is disabled. Set METRICS_ENABLED=true to enable."}
        )
        
    # Pro Mode: Check Authentication Token
    expected_token = os.getenv("METRICS_TOKEN", "").strip()
    if not expected_token:
        # If enabled but no token is set, it's a misconfiguration. Fail secure.
        logger.error("METRICS_ENABLED is true but METRICS_TOKEN is not set. Denying access.")
        return JSONResponse(
            status_code=500,
            content={"error": "CONFIGURATION_ERROR", "message": "Metrics token is not configured on the server."}
        )
        
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
            content={"error": "UNAUTHORIZED", "message": "Missing or invalid Authorization header"}
        )
        
    provided_token = auth_header.split(" ")[1]
    
    # Use constant-time comparison to prevent timing attacks, though simple string 
    # equality is usually acceptable here it's best practice.
    import hmac
    if not hmac.compare_digest(provided_token.encode(), expected_token.encode()):
        return JSONResponse(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
            content={"error": "UNAUTHORIZED", "message": "Invalid metrics token"}
        )
    
    # Authorized Pro User
    content = metrics.get_prometheus_format()
    
    return PlainTextResponse(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )

@app.get("/robots.txt", include_in_schema=False)
async def robots():
    from fastapi.responses import FileResponse
    return FileResponse("app/assets/robots.txt")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    from fastapi.responses import FileResponse
    return FileResponse("app/assets/sitemap.xml")


if __name__ == "__main__":
    import os

    import uvicorn
    
    reload_policy = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload_policy,
        log_level="info"
    )
