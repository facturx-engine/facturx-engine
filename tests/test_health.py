"""
Tests for the /health and /healthz endpoints.
"""
import subprocess
from pathlib import Path
from unittest.mock import patch

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


def test_healthz_executes_saxon_probe(tmp_path):
    fake_jar = tmp_path / "saxon.jar"
    fake_jar.write_bytes(b"fake")

    def successful_probe(command, **kwargs):
        output_arg = next(arg for arg in command if arg.startswith("-o:"))
        Path(output_arg[3:]).write_text("<probe>ok</probe>", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    with patch.dict("os.environ", {"SAXON_JAR": str(fake_jar), "VERAPDF_JAR": ""}):
        with patch("app.main.subprocess.run", side_effect=successful_probe):
            response = TestClient(app).get("/healthz")

    assert response.status_code == 200
    assert response.json()["saxon"]["status"] == "available"


def test_healthz_reports_saxon_execution_failure(tmp_path):
    fake_jar = tmp_path / "saxon.jar"
    fake_jar.write_bytes(b"fake")
    failed = subprocess.CompletedProcess([], 1, stdout=b"", stderr=b"disk full")

    with patch.dict("os.environ", {"SAXON_JAR": str(fake_jar), "VERAPDF_JAR": ""}):
        with patch("app.main.subprocess.run", return_value=failed):
            response = TestClient(app).get("/healthz")

    assert response.status_code == 503
    assert response.json()["saxon"]["status"] == "execution_error"
