import requests
import sys
import os

# Usage: python validate.py <file_path>

API_URL = "http://localhost:8000/v1/validate"

def validate(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(API_URL, files=files)
        
        if response.status_code == 200:
            report = response.json()
            print(f"Valid: {report.get('valid')}")
            print(f"Format: {report.get('format')}")
            if not report.get('valid'):
                print("Errors:", report.get('errors'))
            else:
                print("Success: File is a valid Factur-X/ZUGFeRD invoice.")
        else:
            print(f"Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Connection Error: {e}")
        print("Make sure Docker container is running on port 8000")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate.py <file.pdf>")
        sys.exit(1)
    validate(sys.argv[1])
