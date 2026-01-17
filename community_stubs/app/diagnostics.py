"""
Limited diagnostics for Community Edition.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.version import __version__

router = APIRouter(tags=["diagnostics"])

class SimpleDiagnostics(BaseModel):
    version: str = Field(..., description="Application version")
    edition: str = Field("Community", description="Edition type")
    upgrade_url: str = Field("https://facturx-engine.com/buy", description="Upgrade URL")

@router.get("/diagnostics", response_model=SimpleDiagnostics)
async def get_diagnostics():
    """
    Get basic application version.
    
    For full system diagnostics (memory, environment, config, uptime),
    upgrade to Factur-X Engine Pro.
    """
    return SimpleDiagnostics(
        version=__version__,
        edition="Community"
    )
