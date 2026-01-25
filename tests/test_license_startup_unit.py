from fastapi.testclient import TestClient
from app.main import app
import os
import pytest
import sys
from unittest.mock import patch, MagicMock

def test_startup_crash_on_invalid_key():
    print("\n[TEST] Startup Crash on Invalid Key")
    os.environ["LICENSE_KEY"] = "INVALID_KEY_123"
    
    # Mock is_licensed to return False
    with patch("app.license.is_licensed", return_value=False):
        # Mock sys.exit to verify it's called without actually killing the test process
        with patch("sys.exit") as mock_exit:
            
            # This will run lifespan. Since sys.exit is mocked, it will continue to startup.
            # That's fine for the test, we just want to know sys.exit(1) was triggered.
            with TestClient(app):
                pass
            
            mock_exit.assert_called_with(1)
            print("✅ SUCCESS: sys.exit(1) was called.")

def test_startup_success_no_key():
    print("\n[TEST] Startup Success No Key (Demo)")
    if "LICENSE_KEY" in os.environ:
        del os.environ["LICENSE_KEY"]
    
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
    print("✅ SUCCESS: App started in Demo Mode")

def test_startup_success_valid_key():
    print("\n[TEST] Startup Success Valid Key (Pro)")
    os.environ["LICENSE_KEY"] = "VALID_KEY_777"
    
    with patch("app.license.is_licensed", return_value=True):
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
    print("✅ SUCCESS: App started in Pro Mode")
