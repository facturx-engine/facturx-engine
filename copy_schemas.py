
import shutil
import os
from pathlib import Path

# Source Base
src_base = Path(r"temp_schemas\_Factur-X 1.08 Zugferd 2.4 - 2025 12 04 - FINAL FR\4. FACTUR-X_1.08_XSD_SCHEMATRON_2025-12-04")

# Targets
targets = [
    {
        "src_dir": src_base / "2. Factur-X_1.08_BASIC/_XSLT_BASIC",
        "dest_dir": Path("app/resources/schemas/_XSLT_BASIC"),
        "files": ["FACTUR-X_BASIC.xslt", "FACTUR-X_BASIC_codedb.xml"]
    },
    {
        "src_dir": src_base / "0. Factur-X_1.08_MINIMUM/_XSLT_MINIMUM",
        "dest_dir": Path("app/resources/schemas/_XSLT_MINIMUM"),
        "files": ["FACTUR-X_MINIMUM.xslt", "FACTUR-X_MINIMUM_codedb.xml"]
    },
    {
        "src_dir": src_base / "1. Factur-X_1.08_BASICWL/_XSLT_BASICWL",
        "dest_dir": Path("app/resources/schemas/_XSLT_BASICWL"),
        "files": ["FACTUR-X_BASIC-WL.xslt", "FACTUR-X_BASIC-WL_codedb.xml"]
    }
]

for target in targets:
    try:
        os.makedirs(target["dest_dir"], exist_ok=True)
        for filename in target["files"]:
            src = target["src_dir"] / filename
            dest = target["dest_dir"] / filename
            if src.exists():
                shutil.copy2(src, dest)
                print(f"Copied {filename} to {target['dest_dir']}")
            else:
                print(f"ERROR: Source file not found: {src}")
    except Exception as e:
        print(f"Error processing {target['dest_dir']}: {e}")

print("Schema copy completed.")
