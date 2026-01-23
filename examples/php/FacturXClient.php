<?php

class FacturXClient {
    private $apiUrl;

    public function __construct($apiUrl = "http://localhost:8000") {
        $this->apiUrl = $apiUrl;
    }

    /**
     * Generate a Factur-X PDF from a standard PDF and metadata.
     */
    public function generate($pdfPath, $metadata, $outputPath) {
        if (!file_exists($pdfPath)) {
            throw new Exception("File not found: $pdfPath");
        }

        $ch = curl_init();
        
        // Prepare multipart form data
        $postFields = [
            'pdf' => new CURLFile($pdfPath),
            'metadata' => json_encode($metadata)
        ];

        curl_setopt($ch, CURLOPT_URL, $this->apiUrl . "/v1/convert");
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $postFields);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        
        // Execute request
        $result = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        
        if (curl_errno($ch)) {
            $error = curl_error($ch);
            curl_close($ch);
            throw new Exception("Curl Error: " . $error);
        }
        
        curl_close($ch);

        if ($httpCode !== 200) {
             throw new Exception("API Error ($httpCode): " . $result);
        }

        // Save output
        if (file_put_contents($outputPath, $result) === false) {
             throw new Exception("Failed to write output file: $outputPath");
        }

        return true;
    }
}

// Usage Example:
// try {
//     $client = new FacturXClient();
//     $metadata = [
//         "invoice_number" => "INV-2024-001",
//         "buyer" => ["name" => "Client SAS"],
//         "amounts" => ["grand_total" => "120.00"]
//     ];
//     $client->generate("invoice.pdf", $metadata, "invoice_facturx.pdf");
//     echo "Success!";
// } catch (Exception $e) {
//     echo "Error: " . $e->getMessage();
// }
?>
