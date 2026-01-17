"""
Support bundle generation tool.

Generates a ZIP file with diagnostics, logs, and configuration for troubleshooting.

Usage:
    python -m tools.support_bundle

Output:
    support_bundle.zip in current directory
"""
import os
import json
import zipfile
import requests
from datetime import datetime
from pathlib import Path


def generate_support_bundle():
    """Generate a support bundle ZIP file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_name = f"support_bundle_{timestamp}.zip"
    
    print(f"Generating support bundle: {bundle_name}")
    
    with zipfile.ZipFile(bundle_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. Get diagnostics from API
        try:
            print("- Fetching /diagnostics...")
            resp = requests.get("http://localhost:8000/diagnostics", timeout=5)
            if resp.status_code == 200:
                zf.writestr("diagnostics.json", json.dumps(resp.json(), indent=2))
                print("  ✓ Diagnostics collected")
            else:
                zf.writestr("diagnostics_error.txt", f"Error: HTTP {resp.status_code}")
        except Exception as e:
            zf.writestr("diagnostics_error.txt", f"Error: {str(e)}")
            print(f"  ✗ Could not fetch diagnostics: {e}")
        
        # 2. Get health check
        try:
            print("- Fetching /health...")
            resp = requests.get("http://localhost:8000/health", timeout=5)
            zf.writestr("health.json", json.dumps(resp.json(), indent=2))
            print("  ✓ Health check collected")
        except Exception as e:
            zf.writestr("health_error.txt", f"Error: {str(e)}")
        
        # 3. Environment info (non-sensitive)
        print("- Collecting environment info...")
        env_info = {
            "timestamp": timestamp,
            "cwd": os.getcwd(),
            "python_version": os.sys.version,
            "env_vars_safe": {
                key: value for key, value in os.environ.items()
                if "KEY" not in key.upper() and "SECRET" not in key.upper() and "PASSWORD" not in key.upper()
            }
        }
        zf.writestr("environment.json", json.dumps(env_info, indent=2))
        print("  ✓ Environment info collected")
        
        # 4. Version file
        try:
            version_file = Path("app/version.py")
            if version_file.exists():
                zf.write(version_file, "version.py")
                print("  ✓ Version file collected")
        except Exception as e:
            print(f"  ✗ Could not collect version: {e}")
        
        # 5. Configuration (sanitized)
        try:
            env_example = Path("deploy/selfhosted/.env.example")
            if env_example.exists():
                zf.write(env_example, "env_example.txt")
                print("  ✓ Configuration template collected")
        except:
            pass
    
    print(f"\n✓ Support bundle created: {bundle_name}")
    print(f"  Size: {os.path.getsize(bundle_name) / 1024:.1f} KB")
    print(f"\nSend this file to support for assistance.")
    
    return bundle_name


if __name__ == "__main__":
    try:
        bundle = generate_support_bundle()
    except Exception as e:
        print(f"ERROR: Failed to generate support bundle: {e}")
        exit(1)
