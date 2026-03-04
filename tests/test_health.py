"""
Tests for the /health and /healthz endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app


def test_health_returns_healthy():
    """Test that /health (liveness) returns status healthy with version info."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "factur-x-api"
    assert "version" in data
    assert data["version"]  # Not empty


def test_healthz_returns_readiness_status():
    """Test that /healthz (readiness) returns subsystem details."""
    client = TestClient(app)
    response = client.get("/healthz")

    assert response.status_code in (200, 503)
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "factur-x-api"
    assert "version" in data
    assert "verapdf" in data
    assert "saxon" in data
