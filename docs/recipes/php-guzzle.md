# Recipe: PHP (Guzzle)

Best for Symfony, Laravel, or WordPress integrations.

## Prerequisites

- PHP 8.1+
- `guzzlehttp/guzzle` (`composer require guzzlehttp/guzzle`)

## Implementation

```php
<?php
require 'vendor/autoload.php';

use GuzzleHttp\Client;

$client = new Client();

try {
    $response = $client->post('http://localhost:8000/v1/convert', [
        'multipart' => [
            [
                'name'     => 'pdf',
                'contents' => fopen('input.pdf', 'r'),
                'filename' => 'input.pdf'
            ],
            [
                'name'     => 'metadata',
                'contents' => json_encode([
                    'invoice_id' => 'PHP-999',
                    'seller' => ['name' => 'PHP Solutions'],
                    'totals' => ['net_amount' => 120.50]
                ])
            ]
        ]
    ]);

    file_put_contents('factur-x-final.pdf', $response->getBody());
    echo "Success: File generated.";

} catch (\Exception $e) {
    echo "Error: " . $e->getMessage();
}
```

## Why use an API vs native PHP libs?

PHP native libraries for PDF/A-3 often rely on complex system wrappers (`fpdi`, `tcpdf`) that can be fragile during migrations. **Factur-X Engine** abstracts this into a standard HTTP service, meaning your PHP app remains lightweight and cloud-native.
