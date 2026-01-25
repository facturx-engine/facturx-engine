"""
Test de validation finale - Simule un environnement post-build Docker
"""
import os
import sys
import subprocess

# Inject a fake BUILD_DATE for local testing
print("🔧 Simulating Docker build environment...")
print("   Injecting BUILD_DATE into license.py...")

# Read license.py
with open("app/license.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace placeholder with today's date
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")
content_modified = content.replace('BUILD_DATE = "BUILD_DATE_PLACEHOLDER"', f'BUILD_DATE = "{today}"')

# Write to temp file
with open("app/license_temp.py", "w", encoding="utf-8") as f:
    f.write(content_modified)

# Backup original
os.rename("app/license.py", "app/license_backup.py")
os.rename("app/license_temp.py", "app/license.py")

try:
    print(f"   BUILD_DATE set to: {today}")
    print("\n" + "="*60)
    
    # Run the actual test
    result = subprocess.run([sys.executable, "verify_license_flow.py"], 
                          capture_output=False, text=True)
    
    print("="*60)
    
finally:
    # Restore original
    print("\n🔧 Restoring original license.py...")
    os.remove("app/license.py")
    os.rename("app/license_backup.py", "app/license.py")
    print("✅ Cleanup complete")
