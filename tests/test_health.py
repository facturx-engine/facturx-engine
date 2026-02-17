"""
Tests for the /health endpoint.
"""
from fastapi.testclient import TestClient
from app.main import app


def test_health_returns_healthy():
    """Test that /health returns status healthy with version info."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "factur-x-api"
    assert "version" in data
    assert data["version"]  # Not empty
