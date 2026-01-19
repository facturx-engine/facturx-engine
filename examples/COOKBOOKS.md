# Factur-X Engine - OEM Integration Cookbooks

This guide provides "copy-paste" examples to integrate Factur-X Engine into your software stack.  
The engine exposes a standard REST API, making it compatible with any language capable of HTTP requests.

---

## 🐍 Python (Requests)

Ideal for backend workers or Django/FastAPI/Flask integrations.

**Scenario**: You have a PDF invoice and want the JSON data.

```python
import requests
import json

API_URL = "http://localhost:8000/v1/extract"
FILE_PATH = "invoice.pdf"

def extract_invoice_data():
    with open(FILE_PATH, "rb") as f:
        files = {"file": (FILE_PATH, f, "application/pdf")}
        
        try:
            response = requests.post(API_URL, files=files, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("xml_extracted"):
                print("✅ Success! Extracted Profile:", data["profile_detected"])
                print("Total Amount:", data["invoice_json"]["totals"]["gross_amount"])
            else:
                print("⚠️ Valid PDF, but no Factur-X XML found.")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")

if __name__ == "__main__":
    extract_invoice_data()
```

---

## ☕ Node.js (Axios)

Common in SaaS backends (NestJS, Express).

**Scenario**: Same as above, asynchronous extraction.

```javascript
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

const API_URL = 'http://localhost:8000/v1/extract';
const FILE_PATH = './invoice.pdf';

async function extractInvoice() {
  try {
    const form = new FormData();
    form.append('file', fs.createReadStream(FILE_PATH));

    const response = await axios.post(API_URL, form, {
      headers: {
        ...form.getHeaders(),
      },
    });

    const data = response.data;

    if (data.xml_extracted) {
      console.log('✅ Extracted JSON:', JSON.stringify(data.invoice_json.totals, null, 2));
    } else {
      console.log('⚠️ No Factur-X data found.');
    }
  } catch (error) {
    if (error.response) {
      console.error('❌ Server Error:', error.response.status, error.response.data);
    } else {
      console.error('❌ Connection Error:', error.message);
    }
  }
}

extractInvoice();
```

---

## #️⃣ C# (.NET Core)

Standard for Enterprise ERPs.

**Scenario**: Calling the engine from a sturdy .NET service.

```csharp
using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

class Program
{
    private static readonly HttpClient client = new HttpClient();

    static async Task Main(string[] args)
    {
        var filePath = "invoice.pdf";
        var apiUrl = "http://localhost:8000/v1/extract";

        using (var multipartFormContent = new MultipartFormDataContent())
        {
            // Load the file and add it to the multipart form
            var fileStream = File.OpenRead(filePath);
            var fileStreamContent = new StreamContent(fileStream);
            fileStreamContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/pdf");
            
            // "file" is the form field name expected by FastAPI
            multipartFormContent.Add(fileStreamContent, name: "file", fileName: "invoice.pdf");

            try
            {
                var response = await client.PostAsync(apiUrl, multipartFormContent);
                response.EnsureSuccessStatusCode();
                
                var jsonResponse = await response.Content.ReadAsStringAsync();
                Console.WriteLine("✅ Response Received:");
                Console.WriteLine(jsonResponse);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error: {ex.Message}");
            }
        }
    }
}
```

---

## 🔄 Health Check Pattern

Before sending a batch of files, it is best practice to check if the engine is ready.

**Endpoint**: `GET /health` (if implemented) or simply try a lightweight extraction.

*Note: In the current version v1.0.6, the most reliable health check is to hit the documentation endpoint or a simple extraction.*

```bash
curl -I http://localhost:8000/docs
# HTTP/1.1 200 OK -> Engine is UP
```
