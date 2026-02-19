
import zipfile
import os
from pathlib import Path

zip_path = r"C:\Users\pasca\Downloads\Factur-X-1.08-Zugferd-2.4-2025-12-04-FINAL-FR.zip"
dest_dir = Path("temp_schemas")

if not os.path.exists(zip_path):
    print(f"Error: Zip file not found: {zip_path}")
    exit(1)

print(f"Unzipping {zip_path} to {dest_dir.absolute()}...")

try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            # Filter garbage
            if file.startswith("__MACOSX") or "Icon" in file or "\r" in file:
                continue
            if file.endswith(("/", "\\")):
                continue
                
            try:
                zip_ref.extract(file, dest_dir)
                print(f"Extracted: {file}")
            except Exception as e:
                print(f"Failed to extract {file}: {e}")
                
    print("Done.")
except Exception as e:
    print(f"Error unzipping: {e}")
