import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)

def test_dos_protection_header_check():
    """
    Test that the middleware rejects requests with Content-Length > 20MB.
    """
    # 25 MB
    big_size = 25 * 1024 * 1024
    
    # We manually set the header to simulate a big file announcement
    # Note: TestClient won't actually send 25MB of data here, just the header
    response = client.post(
        "/v1/extract",
        headers={"Content-Length": str(big_size)},
        data=b"not actually 25mb" 
    )
    
    assert response.status_code == 413
    assert "File too large" in response.text

def test_normal_upload_passes_middleware():
    """
    Test that a small file passes the middleware (and fails later if invalid).
    """
    small_file = io.BytesIO(b"%PDF-1.4...")
    
    response = client.post(
        "/v1/extract",
        files={"file": ("test.pdf", small_file, "application/pdf")}
    )
    
    # 400 means it passed middleware but failed validation
    # 200 means it somehow passed validation (unlikely but middleware logic is sound)
    assert response.status_code in [200, 400]
    assert response.status_code != 413
