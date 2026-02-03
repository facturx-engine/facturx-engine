# Factur-X Engine Integration Guide

This guide provides standard recipes to integrate **Factur-X Engine** into your production environment.
Because the engine is a standard REST API, it is compatible with **any programming language** capable of making HTTP requests.

## Python (Requests)

Ideal for internal tooling or FastAPI/Django backends.

```python
import requests
import json

def generate_invoice(pdf_path, metadata):
    url = "http://localhost:8000/v1/convert"
    
    # Multipart upload
    files = {
        'pdf': open(pdf_path, 'rb'),
    }
    # Metadata as form field
    data = {
        'metadata': json.dumps(metadata)
    }

    response = requests.post(url, files=files, data=data)
    response.raise_for_status()
    
    with open("output_factur_x.pdf", "wb") as f:
        f.write(response.content)

# Usage
generate_invoice("invoice.pdf", {"invoice_id": "INV-001"})
```

[View Full Recipe](https://facturx-engine.github.io/facturx-engine/tutorials/python-facturx.html)

---

## Node.js (Axios)

Standard for Express, NestJS, or serverless functions.

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function convert() {
  const form = new FormData();
  form.append('pdf', fs.createReadStream('invoice.pdf'));
  form.append('metadata', JSON.stringify({ invoice_id: "INV-001" }));

  const response = await axios.post('http://localhost:8000/v1/convert', form, {
    headers: { ...form.getHeaders() },
    responseType: 'arraybuffer' // Critical for binary PDF download
  });

  fs.writeFileSync('output_factur_x.pdf', response.data);
}
```

[View Full Recipe](https://facturx-engine.github.io/facturx-engine/tutorials/nodejs-facturx.html)

---

## PHP (Guzzle)

Standard for Symfony, Laravel, and legacy applications.

```php
use GuzzleHttp\Client;

$client = new Client();
$response = $client->post('http://localhost:8000/v1/convert', [
    'multipart' => [
        [
            'name'     => 'pdf',
            'contents' => fopen('invoice.pdf', 'r')
        ],
        [
            'name'     => 'metadata',
            'contents' => json_encode(['invoice_id' => 'INV-001'])
        ]
    ]
]);

file_put_contents('output_factur_x.pdf', $response->getBody());
```

[View Full Recipe](https://facturx-engine.github.io/facturx-engine/tutorials/php-facturx.html)

---

## C# (.NET)

For enterprise integrations.

```csharp
using var client = new HttpClient();
using var content = new MultipartFormDataContent();

var fileStream = File.OpenRead("invoice.pdf");
content.Add(new StreamContent(fileStream), "pdf", "invoice.pdf");
content.Add(new StringContent("{\"invoice_id\": \"INV-001\"}"), "metadata");

var response = await client.PostAsync("http://localhost:8000/v1/convert", content);
var bytes = await response.Content.ReadAsByteArrayAsync();

await File.WriteAllBytesAsync("output_factur_x.pdf", bytes);
```

---

## Java (Spring WebClient)

```java
MultipartBodyBuilder builder = new MultipartBodyBuilder();
builder.part("pdf", new FileSystemResource("invoice.pdf"));
builder.part("metadata", "{\"invoice_id\": \"INV-001\"}");

WebClient.create("http://localhost:8000")
    .post()
    .uri("/v1/convert")
    .contentType(MediaType.MULTIPART_FORM_DATA)
    .body(BodyInserters.fromMultipartData(builder.build()))
    .retrieve()
    .bodyToMono(byte[].class)
    .subscribe(bytes -> Files.write(Paths.get("output.pdf"), bytes));
```
