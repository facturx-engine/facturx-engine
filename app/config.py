from pathlib import Path

# Base directories
# Use resolve() to ensure absolute paths and handle symbolic links correctly
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

# Resource directories
TEMPLATES_DIR = BASE_DIR / "templates"
RESOURCES_DIR = BASE_DIR / "resources"
ASSETS_DIR = BASE_DIR / "assets"

# Specific resource paths
SCHEMATRON_DIR = ASSETS_DIR / "schematron"
SCHEMAS_DIR = RESOURCES_DIR / "schemas"

# Critical artifacts
XSD_PATH = SCHEMAS_DIR / "Factur-X_1.08_EN16931.xsd"
XSLT_PATH = SCHEMAS_DIR / "_XSLT_EN16931" / "FACTUR-X_EN16931.xslt"
