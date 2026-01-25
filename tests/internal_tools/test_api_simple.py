# test_api_simple.py - Script Python pour tester l'API

import requests
import json
from pathlib import Path

print("=" * 60)
print("TEST FACTUR-X API")
print("=" * 60)

API_URL = "http://localhost:8000"

# 1. Test de sante
print("\n[1/5] Test de sante du serveur...")
try:
    health = requests.get(f"{API_URL}/health").json()
    print(f"  OK - Serveur actif : {health['status']}")
except Exception as e:
    print(f"  ERREUR - Serveur non accessible : {e}")
    print("  Lancez : uvicorn app.main:app --port 8000")
    exit(1)

# 2. Creer un PDF de test
print("\n[2/5] Creation du PDF de test...")
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    
    c = canvas.Canvas("invoice_test.pdf", pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "FACTURE")
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, "Numero: TEST-2024-001")
    c.drawString(100, 700, "Date: 13/01/2024")
    c.drawString(100, 650, "Vendeur: Ma Societe SARL")
    c.drawString(100, 630, "Client: Client Test SAS")
    c.drawString(100, 580, "Total HT: 1000.00 EUR")
    c.drawString(100, 560, "TVA: 200.00 EUR")
    c.drawString(100, 540, "Total TTC: 1200.00 EUR")
    c.save()
    print("  OK - PDF cree : invoice_test.pdf")
except Exception as e:
    print(f"  ERREUR : {e}")
    exit(1)

# 3. Preparer les metadonnees
print("\n[3/5] Preparation des metadonnees...")
metadata = {
    "invoice_number": "TEST-2024-001",
    "issue_date": "20240113",
    "seller": {
        "name": "Ma Societe SARL",
        "country_code": "FR",
        "vat_number": "FR12345678901"
    },
    "buyer": {
        "name": "Client Test SAS"
    },
    "amounts": {
        "tax_basis_total": "1000.00",
        "tax_total": "200.00",
        "grand_total": "1200.00",
        "due_payable": "1200.00"
    },
    "currency_code": "EUR",
    "profile": "minimum"
}
print("  OK - Metadonnees preparees")

# 4. Conversion PDF -> Factur-X
print("\n[4/5] Conversion en Factur-X...")
try:
    with open("invoice_test.pdf", "rb") as pdf_file:
        response = requests.post(
            f"{API_URL}/v1/convert",
            files={"pdf": pdf_file},
            data={"metadata": json.dumps(metadata)}
        )
    
    if response.status_code == 200:
        with open("facturx_invoice.pdf", "wb") as f:
            f.write(response.content)
        print("  OK - Factur-X PDF cree : facturx_invoice.pdf")
        print(f"  Taille : {len(response.content)} octets")
    else:
        print(f"  ERREUR - Code HTTP {response.status_code}")
        print(f"  Message : {response.text}")
        exit(1)
except Exception as e:
    print(f"  ERREUR : {e}")
    exit(1)

# 5. Validation du PDF Factur-X
print("\n[5/5] Validation du PDF Factur-X...")
try:
    with open("facturx_invoice.pdf", "rb") as f:
        validation = requests.post(
            f"{API_URL}/v1/validate",
            files={"file": f}
        ).json()
    
    print("\n" + "=" * 60)
    print("RESULTAT DE LA VALIDATION")
    print("=" * 60)
    print(f"  Valide    : {validation['valid']}")
    print(f"  Format    : {validation['format']}")
    print(f"  Niveau    : {validation['flavor']}")
    
    if validation['errors']:
        print(f"  Erreurs   : {', '.join(validation['errors'])}")
    else:
        print("  Erreurs   : Aucune")
    
    print("\n" + "=" * 60)
    if validation['valid']:
        print("SUCCES - Tous les tests ont reussi !")
    else:
        print("ECHEC - Des erreurs ont ete detectees")
    print("=" * 60)
    
    print("\nFichiers generes :")
    print("  - invoice_test.pdf (PDF original)")
    print("  - facturx_invoice.pdf (PDF Factur-X)")
    
except Exception as e:
    print(f"  ERREUR : {e}")
    exit(1)
