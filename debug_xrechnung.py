from app.services.validator import ValidationService
from pathlib import Path

file_path = Path("tests/corpus/valid/xrechnung_3.0_standard.xml")
content = file_path.read_bytes()
is_valid, fmt, flavor, errors = ValidationService.validate_file(content, file_path.name)

print(f"File: {file_path.name}")
print(f"Valid: {is_valid}")
print(f"Format: {fmt}")
print(f"Flavor/Level: {flavor}")
print(f"Errors: {errors}")
