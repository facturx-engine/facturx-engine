# Recipe: Node.js (Axios)

Standard integration for Node.js, Express, or NestJS environments.

## Prerequisites

- Node.js 18+
- `axios` and `form-data` libraries (`npm install axios form-data`)

## Implementation

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function convertToFacturX(pdfPath, metadata) {
  const form = new FormData();
  form.append('pdf', fs.createReadStream(pdfPath));
  form.append('metadata', JSON.stringify(metadata));

  try {
    const response = await axios.post('http://localhost:8000/v1/convert', form, {
      headers: {
        ...form.getHeaders(),
      },
      responseType: 'arraybuffer',
    });

    fs.writeFileSync('output-factur-x.pdf', response.data);
    console.log('Success: Invoice saved to output-factur-x.pdf');
  } catch (error) {
    console.error('API Error:', error.response ? error.response.data.toString() : error.message);
  }
}

// Example usage
const myMetadata = {
  invoice_id: "NODE-42",
  seller: { name: "JS Services" },
  totals: { net_amount: 50.00 }
};

convertToFacturX('./input.pdf', myMetadata);
```

## AI Tip

If you are using an AI agent (Copilot/Claude/GPT) to generate your frontend code, simply provide this file (or `docs/openapi.json`) to it. It will correctly use the `multipart/form-data` pattern required by the engine.
