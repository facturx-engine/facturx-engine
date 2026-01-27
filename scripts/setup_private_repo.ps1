# Script de Configuration Automatique pour Factur-X Pro (Private Repo Strategy)

$CurrentDir = Get-Location
$ParentDir = (Get-Item $CurrentDir).Parent.FullName
$ProRepoName = "facturx-engine-pro-source"
$ProRepoPath = Join-Path $ParentDir $ProRepoName

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Factur-X Pro - Private Repo Setup      " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Validation du dossier
Write-Host "`n[1] Creation du dossier '$ProRepoName'..."
if (-not (Test-Path $ProRepoPath)) {
    New-Item -ItemType Directory -Path $ProRepoPath | Out-Null
    Write-Host "OK : Dossier cree : $ProRepoPath" -ForegroundColor Green
}
else {
    Write-Host "INFO : Le dossier existe deja." -ForegroundColor Yellow
}

# 2. Copie du Template extractor.py
$ExtractorPath = Join-Path $ProRepoPath "extractor.py"
if (-not (Test-Path $ExtractorPath)) {
    $Content = "# PASTE YOUR REAL PRO CODE HERE`nclass ExtractionService:`n    pass"
    Set-Content -Path $ExtractorPath -Value $Content
    Write-Host "OK : Fichier squelette cree : $ExtractorPath" -ForegroundColor Green
    Write-Host "ACTION : Vous devez coller votre VRAI code Pro dans ce fichier !" -ForegroundColor Red
}
else {
    Write-Host "INFO : Le fichier extractor.py existe deja." -ForegroundColor Yellow
}

# 3. Génération des Clés SSH
Write-Host "`n[2] Generation des Cles SSH..."
$KeyPath = Join-Path $ProRepoPath "deploy_key_rsa"

if (-not (Test-Path $KeyPath)) {
    ssh-keygen -t rsa -b 4096 -f $KeyPath -N "" -q
    Write-Host "OK : Cles SSH generees." -ForegroundColor Green
}
else {
    Write-Host "INFO : Les cles existent deja." -ForegroundColor Yellow
}

# 4. Affichage des Clés
$PublicKey = Get-Content "$KeyPath.pub"
$PrivateKey = Get-Content $KeyPath

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "   CONFIGURATION GITHUB REQUISE           " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "`n1. Sur le Repo PRIVE ($ProRepoName) -> Settings -> Deploy keys" -ForegroundColor White
Write-Host "   Ajoutez cette CLE PUBLIQUE :" -ForegroundColor Gray
Write-Host $PublicKey -ForegroundColor Green

Write-Host "`n2. Sur le Repo PUBLIC (facturx-engine) -> Settings -> Secrets -> Actions" -ForegroundColor White
Write-Host "   Creez un secret nomme 'PRO_REPO_KEY' avec cette CLE PRIVEE :" -ForegroundColor Gray
Write-Host $PrivateKey -ForegroundColor Magenta

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "N'oubliez pas de mettre votre code Pro dans $ProRepoPath/extractor.py et de le pousser sur GitHub !"
