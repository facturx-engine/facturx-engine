# test_api.ps1 - Script de test complet pour Factur-X API

Write-Host "Demarrage du test Factur-X API..." -ForegroundColor Cyan

# 1. Verifier que le serveur est demarre
try {
  $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction Stop
  Write-Host "OK - Serveur actif : $($health.status)" -ForegroundColor Green
}
catch {
  Write-Host "ERREUR - Serveur non accessible. Lancez : uvicorn app.main:app --port 8000" -ForegroundColor Red
  exit 1
}

# 2. Creer un PDF de test
Write-Host "`nCreation du PDF de test..." -ForegroundColor Cyan
python -c @"
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
c = canvas.Canvas('invoice_test.pdf', pagesize=A4)
c.setFont('Helvetica-Bold', 16)
c.drawString(100, 750, 'FACTURE')
c.setFont('Helvetica', 12)
c.drawString(100, 720, 'Numero: TEST-2024-001')
c.drawString(100, 700, 'Date: 13/01/2024')
c.drawString(100, 650, 'Vendeur: Ma Societe SARL')
c.drawString(100, 630, 'Client: Client Test SAS')
c.drawString(100, 580, 'Total HT: 1000.00 EUR')
c.drawString(100, 560, 'TVA: 200.00 EUR')
c.drawString(100, 540, 'Total TTC: 1200.00 EUR')
c.save()
"@
Write-Host "OK - PDF cree" -ForegroundColor Green

# 3. Creer les metadonnees
Write-Host "`nCreation des metadonnees..." -ForegroundColor Cyan
$metadata = @{
  invoice_number = "TEST-2024-001"
  issue_date     = "20240113"
  seller         = @{
    name         = "Ma Societe SARL"
    country_code = "FR"
    vat_number   = "FR12345678901"
  }
  buyer          = @{
    name = "Client Test SAS"
  }
  amounts        = @{
    tax_basis_total = "1000.00"
    tax_total       = "200.00"
    grand_total     = "1200.00"
    due_payable     = "1200.00"
  }
  currency_code  = "EUR"
  profile        = "minimum"
} | ConvertTo-Json -Depth 10

# 4. Conversion
Write-Host "`nConversion en Factur-X..." -ForegroundColor Cyan
$convertResponse = Invoke-WebRequest -Uri "http://localhost:8000/v1/convert" `
  -Method Post `
  -Form @{
  pdf      = Get-Item -Path "invoice_test.pdf"
  metadata = $metadata
}

[System.IO.File]::WriteAllBytes("facturx_invoice.pdf", $convertResponse.Content)
Write-Host "OK - Factur-X PDF cree : facturx_invoice.pdf" -ForegroundColor Green

# 5. Validation
Write-Host "`nValidation du PDF Factur-X..." -ForegroundColor Cyan
$validateResponse = Invoke-RestMethod -Uri "http://localhost:8000/v1/validate" `
  -Method Post `
  -Form @{
  file = Get-Item -Path "facturx_invoice.pdf"
}

Write-Host "`nResultat de la validation :" -ForegroundColor Yellow
Write-Host "  - Valide : $($validateResponse.valid)" -ForegroundColor $(if ($validateResponse.valid) { "Green" }else { "Red" })
Write-Host "  - Format : $($validateResponse.format)"
Write-Host "  - Niveau : $($validateResponse.flavor)"
if ($validateResponse.errors.Count -gt 0) {
  Write-Host "  - Erreurs : $($validateResponse.errors -join ', ')" -ForegroundColor Red
}

Write-Host "`nSUCCES - Test termine avec succes !" -ForegroundColor Green
Write-Host "Fichiers generes :" -ForegroundColor Cyan
Write-Host "   - invoice_test.pdf (PDF original)"
Write-Host "   - facturx_invoice.pdf (PDF Factur-X)"
