param (
    [string]$Version = $(Read-Host -Prompt "Enter Release Version (e.g. v1.0.0)")
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " FACTUR-X ENGINE - RELEASE PUBLISHER" -ForegroundColor Cyan
Write-Host "=========================================="
Write-Host ""

$BuildDate = Get-Date -Format "yyyy-MM-dd"
# Script is in _INTERNAL/scripts, so Root is ../..
$ProjectRoot = Resolve-Path "$PSScriptRoot\..\.."
Write-Host "Build Date: $BuildDate"
Write-Host "Project Root: $ProjectRoot"

# Step 1: Build COMMUNITY (Public)
Write-Host "Step 1: Building COMMUNITY Image ($Version)..." -ForegroundColor Yellow
docker build --target community --no-cache -t facturx-community:$Version $ProjectRoot
if ($LASTEXITCODE -ne 0) { Write-Error "Community Build Failed"; exit 1 }

# Step 2: Build PRO (Private)
Write-Host "Step 2: Building PRO Image ($Version)..." -ForegroundColor Yellow
docker build --target pro --no-cache --build-arg BUILD_DATE=$BuildDate -t facturx-pro:$Version $ProjectRoot
if ($LASTEXITCODE -ne 0) { Write-Error "Pro Build Failed"; exit 1 }

# Step 3: Tag COMMUNITY
Write-Host "Step 3: Tagging Community..." -ForegroundColor Yellow
docker tag facturx-community:$Version pascal/factur-x-community:latest
docker tag facturx-community:$Version pascal/factur-x-community:$Version

# Step 4: Export PRO Tarball
Write-Host "Step 4: Exporting PRO Tarball (facturx-pro-$Version.tar)..." -ForegroundColor Yellow
docker save facturx-pro:$Version -o facturx-pro-$Version.tar

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host " SUCCESS! Release $Version ready."
Write-Host " Public Image: pascal/factur-x-community:$Version"
Write-Host " Private Artifact: facturx-pro-$Version.tar"
Write-Host "=========================================="
