"""
System diagnostics and health check endpoints.
"""
import platform
import sys
import os
import psutil
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, List

from app.version import __version__, __git_hash__, __build_date__

router = APIRouter(tags=["diagnostics"])


class RuntimeConfig(BaseModel):
    """Runtime configuration."""
    mode: str = Field(..., description="Runtime mode (development/production)")
    workers: int = Field(default=1, description="Number of worker processes")
    max_upload_size_mb: int = Field(default=10, description="Maximum upload size in MB")


class EnvironmentInfo(BaseModel):
    """Environment fingerprint."""
    os: str = Field(..., description="Operating system")
    architecture: str = Field(..., description="CPU architecture")
    python_version: str = Field(..., description="Python version")
    hostname: str = Field(..., description="Host machine name")


class MemoryStatus(BaseModel):
    """Memory usage approximation."""
    total_mb: float = Field(..., description="Total system memory in MB")
    available_mb: float = Field(..., description="Available memory in MB")
    process_mb: float = Field(..., description="Current process memory in MB")
    percent_used: float = Field(..., description="System memory usage percentage")


class DependencyVersion(BaseModel):
    """Dependency version info."""
    name: str
    version: str


class DiagnosticsResponse(BaseModel):
    """Complete diagnostics response."""
    version: str = Field(..., description="Application version (SemVer)")
    git_hash: str = Field(..., description="Git commit hash")
    build_date: str = Field(..., description="Build date")
    python_version: str = Field(..., description="Python version")
    dependencies: List[DependencyVersion] = Field(..., description="Key dependency versions")
    runtime_config: RuntimeConfig = Field(..., description="Runtime configuration")
    environment: EnvironmentInfo = Field(..., description="Environment information")
    memory_status: MemoryStatus = Field(..., description="Memory usage")
    features_enabled: List[str] = Field(..., description="Enabled features")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


# Track startup time for uptime calculation
_startup_time = datetime.now()


@router.get("/diagnostics", response_model=DiagnosticsResponse)
async def get_diagnostics():
    """
    Get comprehensive system diagnostics.
    
    Returns detailed information about:
    - Application version and build info
    - Dependency versions
    - Runtime configuration
    - Environment details
    - Memory usage
    - Enabled features
    
    Used for support and troubleshooting.
    """
    # Get dependency versions
    try:
        import facturx
        facturx_version = facturx.VERSION
    except:
        facturx_version = "unknown"
    
    try:
        import lxml
        lxml_version = lxml.etree.__version__
    except:
        lxml_version = "unknown"
    
    try:
        import fastapi
        fastapi_version = fastapi.__version__
    except:
        fastapi_version = "unknown"
    
    dependencies = [
        DependencyVersion(name="factur-x", version=str(facturx_version)),
        DependencyVersion(name="lxml", version=str(lxml_version)),
        DependencyVersion(name="fastapi", version=str(fastapi_version)),
        DependencyVersion(name="python", version=sys.version.split()[0])
    ]
    
    # Runtime configuration (from env or defaults)
    runtime_config = RuntimeConfig(
        mode=os.getenv("APP_MODE", "production"),
        workers=int(os.getenv("WORKERS", 1)),
        max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", 10))
    )
    
    # Environment info
    environment = EnvironmentInfo(
        os=f"{platform.system()} {platform.release()}",
        architecture=platform.machine(),
        python_version=sys.version,
        hostname=platform.node()
    )
    
    # Memory status
    memory = psutil.virtual_memory()
    process = psutil.Process()
    memory_status = MemoryStatus(
        total_mb=round(memory.total / 1024 / 1024, 2),
        available_mb=round(memory.available / 1024 / 1024, 2),
        process_mb=round(process.memory_info().rss / 1024 / 1024, 2),
        percent_used=memory.percent
    )
    
    # Features enabled (check env variables or defaults)
    features_enabled = ["validate", "convert", "extract"]
    if os.getenv("DISABLE_CONVERT") == "true":
        features_enabled.remove("convert")
    
    # LICENSE_KEY check for licensing mode
    has_license = bool(os.getenv("LICENSE_KEY"))
    if not has_license:
        features_enabled.append("mode:community")
    else:
        features_enabled.append("mode:paid")
    
    # Calculate uptime
    uptime = (datetime.now() - _startup_time).total_seconds()
    
    return DiagnosticsResponse(
        version=__version__,
        git_hash=__git_hash__,
        build_date=__build_date__,
        python_version=sys.version.split()[0],
        dependencies=dependencies,
        runtime_config=runtime_config,
        environment=environment,
        memory_status=memory_status,
        features_enabled=features_enabled,
        uptime_seconds=round(uptime, 2)
    )
