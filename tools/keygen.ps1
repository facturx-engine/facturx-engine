<#
.SYNOPSIS
    Générateur de clés Factur-X simplifié.
    Appelle le script Python du dépôt privé adjacent.

.EXAMPLE
    .\keygen.ps1 "Mon Client"
    > Génère une clé Pro valide 1 an (date du jour + 365 jours).

.EXAMPLE
    .\keygen.ps1 "Mon Client" -Days 30
    > Génère une clé d'essai de 30 jours.

.EXAMPLE
    .\keygen.ps1 "Mon Client" -Date "2026-12-31" --Tier "oem"
    > Génère une clé OEM jusqu'à la date spécifique.
#>

param (
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$ClientName,

    [Parameter(Position = 1)]
    [string]$Date = "",

    [int]$Days = 365,

    [string]$Tier = "pro"
)

# 1. Localiser le repo privé (Sibling directory)
$PrivateRepoPath = Resolve-Path "$PSScriptRoot\..\..\facturx-engine-pro-source" -ErrorAction SilentlyContinue

if (-not $PrivateRepoPath) {
    Write-Error "[ERREUR] Impossible de trouver le dossier privé 'facturx-engine-pro-source' au même niveau que ce projet."
    exit 1
}

# 2. Calculer la date si absente
if ([string]::IsNullOrWhiteSpace($Date)) {
    $DateObj = (Get-Date).AddDays($Days)
    $Date = $DateObj.ToString("yyyy-MM-dd")
    Write-Host "[INFO] Date automatique (+ $Days jours) : $Date" -ForegroundColor Gray
}

# 3. Construire la commande
# 3. Construire la commande
# IMPORTANT : On doit se placer dans le dossier du script Python pour qu'il trouve le dossier "keys/"
# qui est relatif a son execution.
Push-Location $PrivateRepoPath

try {
    Write-Host "[GEN] Generation pour '$ClientName' ($Tier) -> $Date" -ForegroundColor Cyan

    # 4. Exécuter
    # On appelle admin_keygen.py directement car on est dans le bon dossier
    python admin_keygen.py sign "$ClientName" "$Date" --tier="$Tier"

    Write-Host "`n[OK] Termine." -ForegroundColor Green
}
catch {
    Write-Error "[ERREUR] Echec lors de la generation."
}
finally {
    Pop-Location
}
